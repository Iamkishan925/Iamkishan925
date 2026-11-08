"""Historical price data (yfinance) - free, good for research/backtests.

For live quotes and execution use a broker adapter (see `brokers/`).
yfinance symbols: stocks "AAPL", "RELIANCE.NS"; forex "EURUSD=X"; gold "GC=F".
"""

from __future__ import annotations

import pandas as pd


def history(symbol: str, period: str = "15y", interval: str = "1d") -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("pip install yfinance to fetch historical data") from e

    df = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=True)
    if df.empty:
        raise ValueError(f"no data returned for {symbol!r}")
    return df[["Open", "High", "Low", "Close", "Volume"]]
