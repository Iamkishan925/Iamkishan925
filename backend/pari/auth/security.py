"""Password hashing (Argon2id), TOTP MFA, session tokens and field encryption."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from cryptography.fernet import Fernet

_ph = PasswordHasher()
# Verified against when the username doesn't exist, so timing doesn't reveal valid usernames.
_DUMMY_HASH = _ph.hash(secrets.token_urlsafe(16))

TOTP_PERIOD = 30
MIN_PASSWORD_LENGTH = 12


def hash_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")
    return _ph.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _ph.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


class Cipher:
    def __init__(self, key: str):
        self._f = Fernet(key.encode())

    def encrypt(self, value: str) -> str:
        return self._f.encrypt(value.encode()).decode()

    def decrypt(self, value: str) -> str:
        return self._f.decrypt(value.encode()).decode()


def new_totp_secret() -> str:
    return pyotp.random_base32()


def totp_uri(secret: str, username: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name="Pari")


def verify_totp(secret: str, code: str, last_step: int, now: float | None = None) -> int | None:
    """Return the matched time step if `code` is valid and newer than `last_step`, else None.

    Accepts one step of clock drift either way. Rejecting steps <= last_step stops a
    code that was already used (e.g. seen over someone's shoulder) from working twice.
    """
    code = code.strip().replace(" ", "")
    if not (code.isdigit() and len(code) == 6):
        return None
    now = time.time() if now is None else now
    totp = pyotp.TOTP(secret)
    current = int(now // TOTP_PERIOD)
    for step in (current - 1, current, current + 1):
        if step > last_step and hmac.compare_digest(totp.at(step * TOTP_PERIOD), code):
            return step
    return None


def new_session_token() -> tuple[str, str, str]:
    """Return (public_id, cookie_token, token_hash). Only the hash is stored."""
    token = secrets.token_urlsafe(32)
    return secrets.token_hex(8), token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
