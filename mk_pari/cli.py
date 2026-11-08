"""Terminal chat with Pari.

    python -m mk_pari.cli EURUSD=X "aaje EURUSD ma trade che?"
    python -m mk_pari.cli --backtest AAPL
"""

from __future__ import annotations

import argparse
import json

from . import backtest, data
from .agent import PariAgent


def main() -> None:
    ap = argparse.ArgumentParser(prog="pari")
    ap.add_argument("symbol", help="yfinance symbol, e.g. AAPL, RELIANCE.NS, EURUSD=X")
    ap.add_argument("question", nargs="?", default="Analyse this and tell me if there is a trade.")
    ap.add_argument("--lang", choices=["gu", "hi", "en"])
    ap.add_argument("--news", nargs="*", help="Alpha Vantage tickers, e.g. AAPL FOREX:EUR")
    ap.add_argument("--backtest", action="store_true", help="only run the 15y SMA 50/200 backtest (no Claude)")
    a = ap.parse_args()

    if a.backtest:
        close = data.history(a.symbol)["Close"]
        print(json.dumps(backtest.run(close, backtest.sma_crossover_signals(close)).as_dict(), indent=2))
        return

    agent = PariAgent()
    r = agent.ask(a.symbol, a.question, a.news, a.lang)
    print(f"\n[data as of {r.as_of}]\n\nPari: {r.view.reply}\n")
    print(f"action={r.view.action} entry={r.view.entry} SL={r.view.stop_loss} TP={r.view.take_profit} "
          f"confidence={r.view.confidence}")
    if r.risk_reasons:
        print("risk:", "; ".join(r.risk_reasons))
    if r.executed:
        print("executed:", r.executed)
    elif r.proposal:
        mode = "LIVE" if agent.settings.is_live else "paper"
        ans = input(f"Place {mode} {r.view.action} {r.proposal.decision.quantity:.4f} {a.symbol}? [y/N] ")
        if ans.strip().lower() in {"y", "yes", "ha", "haa"}:
            print(agent.confirm(r.proposal.id))
        else:
            agent.reject(r.proposal.id)
            print("not placed.")


if __name__ == "__main__":
    main()
