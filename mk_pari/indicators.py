"""Technical indicators in plain pandas (no TA-Lib C dependency needed)."""

from __future__ import annotations

import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window).mean()


def ema(close: pd.Series, span: int) -> pd.Series:
    return close.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Wilder's RSI."""
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    rs = gain / loss
    out = 100 - 100 / (1 + rs)
    return out.where(loss != 0, 100.0).where(gain.notna())


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    line = ema(close, fast) - ema(close, slow)
    sig = ema(line, signal)
    return pd.DataFrame({"macd": line, "signal": sig, "hist": line - sig})


def bollinger(close: pd.Series, window: int = 20, k: float = 2.0) -> pd.DataFrame:
    mid = sma(close, window)
    sd = close.rolling(window).std()
    return pd.DataFrame({"mid": mid, "upper": mid + k * sd, "lower": mid - k * sd})


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Average True Range; df needs High, Low, Close columns."""
    prev_close = df["Close"].shift()
    tr = pd.concat(
        [df["High"] - df["Low"], (df["High"] - prev_close).abs(), (df["Low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()


def snapshot(df: pd.DataFrame) -> dict:
    """Latest indicator values as a compact dict to hand to Claude."""
    close = df["Close"]
    m = macd(close).iloc[-1]
    b = bollinger(close).iloc[-1]

    def r(x):
        return None if pd.isna(x) else round(float(x), 5)

    return {
        "last_close": r(close.iloc[-1]),
        "sma_20": r(sma(close, 20).iloc[-1]),
        "sma_50": r(sma(close, 50).iloc[-1]),
        "sma_200": r(sma(close, 200).iloc[-1]),
        "rsi_14": r(rsi(close).iloc[-1]),
        "macd": r(m["macd"]),
        "macd_signal": r(m["signal"]),
        "bb_upper": r(b["upper"]),
        "bb_lower": r(b["lower"]),
        "atr_14": r(atr(df).iloc[-1]),
        "change_20d_pct": r((close.iloc[-1] / close.iloc[-21] - 1) * 100) if len(close) > 21 else None,
    }
