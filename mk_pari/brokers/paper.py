from __future__ import annotations

import uuid

from .base import Broker, Fill


class PaperBroker(Broker):
    """In-memory simulated account. The default - no real money moves."""

    def __init__(self, starting_equity: float = 100_000.0):
        self._equity = starting_equity
        self.orders: list[Fill] = []

    def equity(self) -> float:
        return self._equity

    def place_bracket_order(self, symbol, side, quantity, entry, stop_loss, take_profit) -> Fill:
        fill = Fill(str(uuid.uuid4()), symbol, side, round(quantity, 4), entry, stop_loss, take_profit, "filled (paper)")
        self.orders.append(fill)
        return fill
