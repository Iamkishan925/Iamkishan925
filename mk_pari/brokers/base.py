from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Fill:
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float | None
    stop_loss: float
    take_profit: float
    status: str


class Broker(ABC):
    """Minimal interface every broker adapter implements (paper, Alpaca, IBKR, MT5...)."""

    @abstractmethod
    def equity(self) -> float: ...

    @abstractmethod
    def place_bracket_order(
        self, symbol: str, side: str, quantity: float, entry: float, stop_loss: float, take_profit: float
    ) -> Fill: ...
