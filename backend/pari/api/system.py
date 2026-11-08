from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from .. import __version__, audit
from ..db import User
from ..deps import current_user, db

router = APIRouter(prefix="/api", tags=["system"])

# Honest module status shown on the dashboard. Change a row only when the module really works.
MODULES = [
    ("auth", "ready", "Password + TOTP login, sessions, lockout"),
    ("audit", "ready", "Activity log"),
    ("chat", "ready", "Conversations are saved; AI replies arrive in Phase 3"),
    ("ai", "planned", "Claude conversations - Phase 3"),
    ("voice", "planned", "Speech-to-text and Pari's voice - Phase 3"),
    ("memory", "planned", "Saved preferences you control - Phase 4"),
    ("integrations", "planned", "Permissioned connectors - Phase 4"),
    ("market_data", "planned", "Forex prices - Phase 5"),
    ("news", "planned", "News and economic calendar - Phase 5"),
    ("analysis", "planned", "Technical analysis - Phase 6"),
    ("strategies", "planned", "Strategy engine - Phase 6"),
    ("backtest", "planned", "Historical backtesting - Phase 7"),
    ("paper_trading", "planned", "Paper trading and risk engine - Phase 8"),
    ("execution", "disabled", "Broker orders - demo only from Phase 9; real money disabled"),
]


@router.get("/health")
def health(request: Request, s: Session = Depends(db)):
    try:
        s.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "error"
    return {"status": "ok" if database == "ok" else "degraded", "version": __version__, "database": database}


@router.get("/status")
def status(_: User = Depends(current_user)):
    return {"modules": [{"name": n, "state": st, "note": note} for n, st, note in MODULES],
            "live_trading": False}


@router.get("/audit")
def activity(limit: int = 50, _: User = Depends(current_user), s: Session = Depends(db)):
    return [{"ts": e.ts, "actor": e.actor, "action": e.action, "ip": e.ip, "detail": e.detail}
            for e in audit.recent(s, limit)]
