from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .auth.security import hash_token
from .config import Settings
from .db import User, UserSession, utcnow

SESSION_COOKIE = "pari_session"


def settings(request: Request) -> Settings:
    return request.app.state.settings


def db(request: Request) -> Iterator[Session]:
    yield from request.app.state.db.session()


def client_ip(request: Request) -> str:
    direct = request.client.host if request.client else ""
    if not request.app.state.settings.trust_proxy:
        return direct[:64]
    # Only our own reverse proxy (Caddy) is trusted; it appends the real client address last,
    # so the rightmost entry is the one a client can't forge.
    fwd = request.headers.get("x-forwarded-for", "")
    return (fwd.split(",")[-1].strip() if fwd else direct)[:64]


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)  # SQLite drops tzinfo


def current_session(request: Request, s: Session = Depends(db), cfg: Settings = Depends(settings)) -> UserSession:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(401, "not signed in")
    sess = s.query(UserSession).filter_by(token_hash=hash_token(token)).one_or_none()
    now = utcnow()
    if sess is None:
        raise HTTPException(401, "not signed in")
    if _aware(sess.expires_at) < now or now - _aware(sess.last_seen) > timedelta(minutes=cfg.session_idle_minutes):
        s.delete(sess)
        s.commit()
        raise HTTPException(401, "session expired")
    if now - _aware(sess.last_seen) > timedelta(minutes=1):  # avoid a write on every request
        sess.last_seen = now
        s.commit()
    return sess


def current_user(sess: UserSession = Depends(current_session), s: Session = Depends(db)) -> User:
    user = s.get(User, sess.user_id)
    if user is None:
        raise HTTPException(401, "not signed in")
    return user
