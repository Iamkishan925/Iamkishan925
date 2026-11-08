"""Alpaca adapter (US stocks/crypto) using its REST API.

Uses the paper endpoint unless live trading is explicitly enabled.
For forex, write a sibling adapter for MetaTrader5 or IBKR (`ib_insync`)
implementing the same `Broker` interface.
"""

from __future__ import annotations

import httpx2 as httpx

from .base import Broker, Fill

PAPER_URL = "https://paper-api.alpaca.markets"
LIVE_URL = "https://api.alpaca.markets"


class AlpacaBroker(Broker):
    def __init__(self, key: str | None, secret: str | None, live: bool = False):
        if not (key and secret):
            raise RuntimeError("ALPACA_API_KEY and ALPACA_API_SECRET are required for the alpaca broker")
        self._client = httpx.Client(
            base_url=LIVE_URL if live else PAPER_URL,
            headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret},
            timeout=15,
        )

    def equity(self) -> float:
        r = self._client.get("/v2/account")
        r.raise_for_status()
        return float(r.json()["equity"])

    def place_bracket_order(self, symbol, side, quantity, entry, stop_loss, take_profit) -> Fill:
        r = self._client.post(
            "/v2/orders",
            json={
                "symbol": symbol,
                "side": side,
                "qty": str(int(quantity)),
                "type": "market",
                "time_in_force": "day",
                "order_class": "bracket",
                "take_profit": {"limit_price": round(take_profit, 2)},
                "stop_loss": {"stop_price": round(stop_loss, 2)},
            },
        )
        r.raise_for_status()
        o = r.json()
        return Fill(o["id"], symbol, side, float(o["qty"]), None, stop_loss, take_profit, o["status"])
