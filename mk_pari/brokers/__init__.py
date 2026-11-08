from __future__ import annotations

from ..config import Settings
from .base import Broker
from .paper import PaperBroker


def get_broker(settings: Settings) -> Broker:
    if settings.broker == "paper":
        return PaperBroker()
    if settings.broker == "alpaca":
        from .alpaca import AlpacaBroker

        return AlpacaBroker(settings.alpaca_key, settings.alpaca_secret, live=settings.is_live)
    raise ValueError(f"unknown broker {settings.broker!r}")


__all__ = ["Broker", "PaperBroker", "get_broker"]
