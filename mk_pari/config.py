"""Runtime configuration, read only from environment variables.

Secrets (broker keys, news keys, TTS keys, Anthropic key) never live in code.
Copy `.env.example` to `.env` locally, or set them as secrets on the server.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


@dataclass(frozen=True)
class RiskLimits:
    max_risk_per_trade_pct: float = 1.0  # % of equity risked between entry and stop
    max_position_pct: float = 10.0  # max notional per position, % of equity
    max_daily_loss_pct: float = 3.0  # trading halts for the day beyond this
    min_reward_risk: float = 1.5  # take-profit distance / stop distance


@dataclass(frozen=True)
class Settings:
    broker: str = "paper"  # paper | alpaca
    # Live trading needs BOTH flags: LIVE_TRADING=true and a broker other than paper.
    live_trading: bool = False
    # Every order Claude proposes waits for a human "yes" unless this is turned on.
    auto_execute: bool = False
    language: str = "gu"  # gu | hi | en - default reply language
    claude_model: str = "claude-opus-5-5"
    claude_effort: str = "high"
    alpha_vantage_key: str | None = None
    elevenlabs_key: str | None = None
    elevenlabs_voice_id: str | None = None
    alpaca_key: str | None = None
    alpaca_secret: str | None = None
    api_token: str | None = None  # bearer token protecting the web API
    risk: RiskLimits = field(default_factory=RiskLimits)

    @property
    def is_live(self) -> bool:
        return self.live_trading and self.broker != "paper"


def load_settings() -> Settings:
    return Settings(
        broker=os.getenv("BROKER", "paper"),
        live_trading=_bool("LIVE_TRADING"),
        auto_execute=_bool("AUTO_EXECUTE"),
        language=os.getenv("PARI_LANGUAGE", "gu"),
        claude_model=os.getenv("CLAUDE_MODEL", "claude-opus-5-5"),
        claude_effort=os.getenv("CLAUDE_EFFORT", "high"),
        alpha_vantage_key=os.getenv("ALPHA_VANTAGE_API_KEY"),
        elevenlabs_key=os.getenv("ELEVENLABS_API_KEY"),
        elevenlabs_voice_id=os.getenv("ELEVENLABS_VOICE_ID"),
        alpaca_key=os.getenv("ALPACA_API_KEY"),
        alpaca_secret=os.getenv("ALPACA_API_SECRET"),
        api_token=os.getenv("PARI_API_TOKEN"),
        risk=RiskLimits(
            max_risk_per_trade_pct=_float("MAX_RISK_PER_TRADE_PCT", 1.0),
            max_position_pct=_float("MAX_POSITION_PCT", 10.0),
            max_daily_loss_pct=_float("MAX_DAILY_LOSS_PCT", 3.0),
            min_reward_risk=_float("MIN_REWARD_RISK", 1.5),
        ),
    )
