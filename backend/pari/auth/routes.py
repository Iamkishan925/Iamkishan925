from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import audit
from ..config import Settings
from ..db import User, UserSession, utcnow
from ..deps import SESSION_COOKIE, client_ip, current_session, current_user, db, settings
from .security import new_session_token, verify_password, verify_totp

router = APIRouter(prefix="/api/auth", tags=["auth"])

GENERIC_FAIL = "username, password or code is incorrect"


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)
    totp: str = Field(min_length=6, max_length=8)


@router.post("/login")
def login(body: LoginIn, request: Request, response: Response, s: Session = Depends(db),
          cfg: Settings = Depends(settings)):
    ip = client_ip(request)
    limiter = request.app.state.login_limiter
    keys = (f"user:{body.username.lower()}", f"ip:{ip}")
    if limiter.blocked(*keys):
        audit.record(s, body.username, "login_blocked", ip)
        raise HTTPException(429, "too many failed attempts, try again later")

    user = s.query(User).filter_by(username=body.username).one_or_none()
    ok_pw = verify_password(user.password_hash if user else None, body.password)
    step = None
    if user and ok_pw:
        step = verify_totp(request.app.state.cipher.decrypt(user.totp_secret_enc), body.totp, user.last_totp_step)
    if not (user and ok_pw and step):
        limiter.fail(*keys)
        audit.record(s, body.username, "login_failed", ip, reason="password" if not ok_pw else "totp")
        raise HTTPException(401, GENERIC_FAIL)

    limiter.reset(*keys)
    user.last_totp_step = step
    public_id, token, token_hash = new_session_token()
    now = utcnow()
    s.add(UserSession(id=public_id, token_hash=token_hash, user_id=user.id, created_at=now, last_seen=now,
                      expires_at=now + timedelta(days=cfg.session_max_days), ip=ip,
                      user_agent=request.headers.get("user-agent", "")[:256]))
    s.commit()
    response.set_cookie(SESSION_COOKIE, token, httponly=True, secure=cfg.cookie_secure, samesite="strict",
                        max_age=cfg.session_max_days * 86400, path="/")
    audit.record(s, user.username, "login", ip, session=public_id)
    return {"username": user.username, "display_name": user.display_name}


@router.post("/logout")
def logout(request: Request, response: Response, sess: UserSession = Depends(current_session),
           user: User = Depends(current_user), s: Session = Depends(db)):
    s.delete(s.merge(sess))
    s.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")
    audit.record(s, user.username, "logout", client_ip(request), session=sess.id)
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"username": user.username, "display_name": user.display_name}


@router.get("/sessions")
def sessions(sess: UserSession = Depends(current_session), s: Session = Depends(db)):
    rows = s.query(UserSession).filter_by(user_id=sess.user_id).order_by(UserSession.created_at.desc()).all()
    return [
        {"id": r.id, "created_at": r.created_at, "last_seen": r.last_seen, "ip": r.ip, "user_agent": r.user_agent,
         "current": r.id == sess.id}
        for r in rows
    ]


@router.delete("/sessions/{session_id}")
def revoke(session_id: str, request: Request, sess: UserSession = Depends(current_session),
           user: User = Depends(current_user), s: Session = Depends(db)):
    target = s.query(UserSession).filter_by(id=session_id, user_id=sess.user_id).one_or_none()
    if target is None:
        raise HTTPException(404, "no such session")
    s.delete(target)
    s.commit()
    audit.record(s, user.username, "session_revoked", client_ip(request), session=session_id)
    return {"ok": True}
