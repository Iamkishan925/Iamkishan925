"""Pari's reasoning: Claude reads market data + news and returns a structured view.

Claude only *proposes*. `risk.evaluate` and the human-confirmation step in
`agent.py` decide whether anything is executed.
"""

from __future__ import annotations

import json
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are Pari, the personal trading assistant of MK. You speak Gujarati, Hindi and \
English and reply in the language MK asks for (default given in each request). You are comfortable \
with numbers and show the key maths (risk, reward/risk, position size) briefly.

You are given, for one symbol: a timestamped indicator snapshot, a long-history backtest summary, and \
recent news headlines with sentiment. Base every statement on that data; if it is missing or stale, \
say so instead of guessing. Mention the data timestamp in your reply.

When the evidence supports a trade, propose one with an entry, stop-loss and take-profit (use ATR for \
distances). Otherwise recommend "hold". Be honest about uncertainty - markets are noisy and a \
backtest is not a forecast. Never mention API keys or internal configuration.

Your proposal goes to a separate risk engine and to MK for confirmation; you never place orders \
yourself."""

LANG_NAMES = {"gu": "Gujarati", "hi": "Hindi", "en": "English"}


class PariView(BaseModel):
    action: Literal["buy", "sell", "hold"]
    entry: float | None = Field(None, description="Proposed entry price; null for hold")
    stop_loss: float | None = None
    take_profit: float | None = None
    confidence: Literal["low", "medium", "high"]
    reasoning: str = Field(description="Short technical/news rationale in English, for the log")
    reply: str = Field(description="Friendly reply to MK in the requested language, suitable to read aloud")


class PariRefused(RuntimeError):
    pass


class Brain:
    def __init__(self, model: str = "claude-opus-5-5", effort: str = "high", client: anthropic.Anthropic | None = None):
        self.model = model
        self.effort = effort
        self.client = client or anthropic.Anthropic()

    def analyse(
        self,
        symbol: str,
        as_of: str,
        snapshot: dict,
        backtest: dict | None,
        news: list[dict],
        question: str,
        language: str = "gu",
    ) -> PariView:
        context = {
            "symbol": symbol,
            "data_as_of": as_of,
            "indicators": snapshot,
            "backtest_sma50_200_15y": backtest,
            "news": news,
        }
        user = (
            f"<market_data>\n{json.dumps(context, ensure_ascii=False, indent=1)}\n</market_data>\n\n"
            f"Reply language: {LANG_NAMES.get(language, language)}\n\n"
            f"MK asks: {question}"
        )
        response = self.client.beta.messages.parse(
            model=self.model,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            output_config={"effort": self.effort},
            output_format=PariView,
            # Server-side fallback: if a safety classifier declines, the API retries on a
            # suitable model inside the same call.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": user}],
        )
        if response.stop_reason == "refusal":
            raise PariRefused("Claude declined this request")
        if response.parsed_output is None:
            raise RuntimeError(f"no structured output (stop_reason={response.stop_reason})")
        return response.parsed_output
