from datetime import timedelta

import pyotp
import pytest

from pari.auth.ratelimit import LoginLimiter
from pari.auth.security import hash_password, verify_password, verify_totp
from pari.config import ConfigError, Settings
from pari.db import AuditEvent, UserSession

from .conftest import PASSWORD


def test_password_hashing():
    h = hash_password(PASSWORD)
    assert h.startswith("$argon2id$")
    assert verify_password(h, PASSWORD)
    assert not verify_password(h, PASSWORD + "x")
    assert not verify_password(None, PASSWORD)
    with pytest.raises(ValueError):
        hash_password("short")


def test_totp_window_and_replay():
    secret = pyotp.random_base32()
    t = pyotp.TOTP(secret)
    now = 1_700_000_000
    step = verify_totp(secret, t.at(now), 0, now=now)
    assert step == now // 30
    assert verify_totp(secret, t.at(now), step, now=now) is None  # replay rejected
    assert verify_totp(secret, t.at(now - 30), 0, now=now) is not None  # one step drift ok
    assert verify_totp(secret, t.at(now - 90), 0, now=now) is None
    assert verify_totp(secret, "abc123", 0, now=now) is None


def test_limiter():
    lim = LoginLimiter(3, 60)
    for _ in range(3):
        lim.fail("u", now=0)
    assert lim.blocked("u", now=1)
    assert not lim.blocked("u", now=61)


def test_config_requires_data_key_and_https_in_production():
    with pytest.raises(ConfigError):
        Settings(data_key=None).validate()
    with pytest.raises(ConfigError):
        Settings(env="production", data_key="k", cookie_secure=False,
                 database_url="postgresql+psycopg://x/y").validate()
    with pytest.raises(ConfigError):
        Settings(env="production", data_key="k", cookie_secure=True).validate()  # sqlite


def test_login_flow_and_cookie_flags(client, owner):
    assert client.get("/api/auth/me").status_code == 401
    r = client.post("/api/auth/login", json={"username": "mk", "password": PASSWORD, "totp": owner.now()})
    assert r.status_code == 200
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    assert client.get("/api/auth/me").json()["display_name"] == "MK"
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_wrong_credentials_are_indistinguishable(client, owner):
    bad_pw = client.post("/api/auth/login", json={"username": "mk", "password": "nope", "totp": owner.now()})
    bad_user = client.post("/api/auth/login", json={"username": "x", "password": PASSWORD, "totp": owner.now()})
    bad_code = client.post("/api/auth/login", json={"username": "mk", "password": PASSWORD, "totp": "000000"})
    assert bad_pw.status_code == bad_user.status_code == bad_code.status_code == 401
    assert bad_pw.json() == bad_user.json() == bad_code.json()


def test_lockout_after_failures(client, owner):
    for _ in range(5):
        client.post("/api/auth/login", json={"username": "mk", "password": "wrong", "totp": "123456"})
    r = client.post("/api/auth/login", json={"username": "mk", "password": PASSWORD, "totp": owner.now()})
    assert r.status_code == 429


def test_totp_code_cannot_be_reused(client, owner):
    code = owner.now()
    assert client.post("/api/auth/login", json={"username": "mk", "password": PASSWORD, "totp": code}).status_code == 200
    client.cookies.clear()
    assert client.post("/api/auth/login", json={"username": "mk", "password": PASSWORD, "totp": code}).status_code == 401


def test_session_list_and_revoke(logged_in):
    rows = logged_in.get("/api/auth/sessions").json()
    assert len(rows) == 1 and rows[0]["current"]
    assert logged_in.delete(f"/api/auth/sessions/{rows[0]['id']}").status_code == 200
    assert logged_in.get("/api/auth/me").status_code == 401


def test_idle_session_expires(app, logged_in):
    with app.state.db.SessionLocal() as s:
        sess = s.query(UserSession).one()
        sess.last_seen = sess.last_seen - timedelta(days=1)
        s.commit()
    assert logged_in.get("/api/auth/me").status_code == 401


def test_foreign_origin_blocked(client, owner):
    r = client.post("/api/auth/login", headers={"Origin": "https://evil.example"},
                    json={"username": "mk", "password": PASSWORD, "totp": owner.now()})
    assert r.status_code == 403


def test_audit_log_never_stores_secrets(app, client, owner):
    client.post("/api/auth/login", json={"username": "mk", "password": PASSWORD, "totp": owner.now()})
    with app.state.db.SessionLocal() as s:
        events = s.query(AuditEvent).all()
    blob = repr([(e.action, e.detail) for e in events])
    assert "login" in blob and PASSWORD not in blob
