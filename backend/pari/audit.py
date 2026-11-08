"""Append-only activity log. Every security-relevant action writes here."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import AuditEvent

# Keys that must never be written into the log, even by mistake.
_REDACT = {"password", "totp", "code", "token", "secret", "api_key"}


def record(db: Session, actor: str, action: str, ip: str = "", **detail) -> None:
    clean = {k: ("[redacted]" if k.lower() in _REDACT else v) for k, v in detail.items()}
    db.add(AuditEvent(actor=actor, action=action, ip=ip, detail=clean))
    db.commit()


def recent(db: Session, limit: int = 50) -> list[AuditEvent]:
    return list(db.scalars(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(min(limit, 500))))
