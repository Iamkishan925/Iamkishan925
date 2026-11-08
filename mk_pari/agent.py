"""Orchestrates one request: data -> indicators -> backtest -> news -> Claude -> risk -> (confirm) -> broker."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pandas as pd

from . import backtest, data, indicators, news, risk
from .brain import Brain, PariView
from .brokers import Broker, get_broker
from .config import Settings, load_settings

PROPOSAL_TTL_SECONDS = 300  # a proposal confirmed later than this is refused (prices moved)


@dataclass
class Proposal:
    id: str
    symbol: str
    view: PariView
    decision: risk.RiskDecision
    created: float = field(default_factory=time.time)


@dataclass
class AskResult:
    view: PariView
    as_of: str
    proposal: Proposal | None
    risk_reasons: list[str]
    executed: dict | None = None


class PariAgent:
    def __init__(self, settings: Settings | None = None, brain: Brain | None = None, broker: Broker | None = None,
                 history_fn=data.history, news_fn=news.latest):
        self.settings = settings or load_settings()
        self.brain = brain or Brain(self.settings.claude_model, self.settings.claude_effort)
        self.broker = broker or get_broker(self.settings)
        self._history = history_fn
        self._news = news_fn
        self.pending: dict[str, Proposal] = {}
        self.realized_pnl_today = 0.0

    def ask(self, symbol: str, question: str, news_tickers: list[str] | None = None,
            language: str | None = None) -> AskResult:
        df: pd.DataFrame = self._history(symbol)
        as_of = (df.index[-1].isoformat() if hasattr(df.index[-1], "isoformat") else str(df.index[-1]))
        snap = indicators.snapshot(df)
        bt = backtest.run(df["Close"], backtest.sma_crossover_signals(df["Close"])).as_dict()
        headlines = self._news(self.settings.alpha_vantage_key, news_tickers)

        view = self.brain.analyse(symbol, as_of, snap, bt, headlines, question, language or self.settings.language)
        result = AskResult(view=view, as_of=as_of, proposal=None, risk_reasons=[])
        if view.action == "hold" or None in (view.entry, view.stop_loss, view.take_profit):
            return result

        decision = risk.evaluate(
            risk.OrderProposal(symbol, view.action, view.entry, view.stop_loss, view.take_profit, view.reasoning),
            self.broker.equity(), self.settings.risk, self.realized_pnl_today,
        )
        result.risk_reasons = decision.reasons
        if not decision.approved:
            return result

        prop = Proposal(str(uuid.uuid4())[:8], symbol, view, decision)
        result.proposal = prop
        if self.settings.auto_execute:
            result.executed = self._execute(prop)
        else:
            self.pending[prop.id] = prop
        return result

    def confirm(self, proposal_id: str) -> dict:
        prop = self.pending.pop(proposal_id, None)
        if prop is None:
            raise KeyError("no such pending proposal")
        if time.time() - prop.created > PROPOSAL_TTL_SECONDS:
            raise TimeoutError("proposal expired - ask Pari again for fresh prices")
        return self._execute(prop)

    def reject(self, proposal_id: str) -> None:
        self.pending.pop(proposal_id, None)

    def _execute(self, prop: Proposal) -> dict:
        v = prop.view
        fill = self.broker.place_bracket_order(prop.symbol, v.action, prop.decision.quantity, v.entry, v.stop_loss,
                                               v.take_profit)
        return {**fill.__dict__, "mode": "LIVE" if self.settings.is_live else "paper",
                "at": datetime.now(timezone.utc).isoformat()}
