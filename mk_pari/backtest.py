"""Small vectorised backtester for signal-based strategies.

Good enough to sanity-check an idea on 10-15 years of daily data before
moving to Backtrader/VectorBT for anything more detailed.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .indicators import sma


@dataclass
class BacktestResult:
    total_return_pct: float
    cagr_pct: float
    max_drawdown_pct: float
    sharpe: float
    trades: int
    win_rate_pct: float
    buy_hold_return_pct: float

    def as_dict(self) -> dict:
        return {k: round(v, 2) if isinstance(v, float) else v for k, v in self.__dict__.items()}


def sma_crossover_signals(close: pd.Series, fast: int = 50, slow: int = 200) -> pd.Series:
    """1 when fast SMA is above slow SMA, else 0 (long-only)."""
    return (sma(close, fast) > sma(close, slow)).astype(int)


def run(
    close: pd.Series,
    signals: pd.Series,
    cost_bps: float = 5.0,
    periods_per_year: int = 252,
) -> BacktestResult:
    """Positions are taken on the bar *after* the signal to avoid look-ahead bias."""
    close = close.dropna()
    position = signals.reindex(close.index).fillna(0).shift(1).fillna(0)
    rets = close.pct_change().fillna(0)
    turnover = position.diff().abs().fillna(position.abs())
    strat = position * rets - turnover * cost_bps / 10_000

    equity = (1 + strat).cumprod()
    years = max(len(close) / periods_per_year, 1e-9)
    total = equity.iloc[-1] - 1
    dd = (equity / equity.cummax() - 1).min()
    sd = strat.std()
    sharpe = float(strat.mean() / sd * np.sqrt(periods_per_year)) if sd > 0 else 0.0

    # Trade-level stats: a trade runs from entry (0->1) to exit (1->0).
    entries = position.diff().fillna(position) > 0
    trade_id = entries.cumsum().where(position > 0)
    trade_rets = (1 + strat).groupby(trade_id).prod() - 1 if trade_id.notna().any() else pd.Series(dtype=float)

    return BacktestResult(
        total_return_pct=float(total * 100),
        cagr_pct=float((equity.iloc[-1] ** (1 / years) - 1) * 100),
        max_drawdown_pct=float(dd * 100),
        sharpe=sharpe,
        trades=int(len(trade_rets)),
        win_rate_pct=float((trade_rets > 0).mean() * 100) if len(trade_rets) else 0.0,
        buy_hold_return_pct=float((close.iloc[-1] / close.iloc[0] - 1) * 100),
    )
