"""Settings come only from environment variables. Nothing secret lives in code."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _list(name: str, default: str) -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    env: str = "development"  # development | production | test
    database_url: str = "sqlite:///./pari-dev.db"
    # Fernet key used to encrypt sensitive fields (TOTP secrets now, memories later).
    data_key: str | None = None
    cookie_secure: bool = False
    trust_proxy: bool = False  # true only when the backend is reachable solely through Caddy
    allowed_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173"])
    session_idle_minutes: int = 12 * 60
    session_max_days: int = 7
    login_max_failures: int = 5
    login_lockout_minutes: int = 15

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    def validate(self) -> None:
        if not self.data_key:
            raise ConfigError("PARI_DATA_KEY is not set. See .env.example for how to generate one.")
        if self.is_production:
            if not self.cookie_secure:
                raise ConfigError("PARI_COOKIE_SECURE must be true in production (HTTPS only).")
            if self.database_url.startswith("sqlite"):
                raise ConfigError("Use PostgreSQL (DATABASE_URL) in production.")


def load_settings() -> Settings:
    env = os.getenv("PARI_ENV", "development")
    return Settings(
        env=env,
        database_url=os.getenv("DATABASE_URL", "sqlite:///./pari-dev.db"),
        data_key=os.getenv("PARI_DATA_KEY") or None,
        cookie_secure=_bool("PARI_COOKIE_SECURE", env == "production"),
        trust_proxy=_bool("PARI_TRUST_PROXY", False),
        allowed_origins=_list("PARI_ALLOWED_ORIGINS", "http://localhost:5173"),
        session_idle_minutes=int(os.getenv("PARI_SESSION_IDLE_MINUTES", 12 * 60)),
        session_max_days=int(os.getenv("PARI_SESSION_MAX_DAYS", 7)),
    )


@lru_cache
def get_settings() -> Settings:
    return load_settings()
