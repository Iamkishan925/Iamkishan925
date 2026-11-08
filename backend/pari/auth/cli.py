"""Owner account setup, run on the server terminal (never through the web).

    python -m pari.auth.cli create-owner --username mk
    python -m pari.auth.cli reset-totp --username mk

The password is typed with getpass (not echoed, not logged). The TOTP setup URI is
printed once in your terminal: add it to an authenticator app (Google Authenticator,
Microsoft Authenticator, 1Password, Aegis...).
"""

from __future__ import annotations

import argparse
import getpass
import sys

from .. import audit
from ..config import get_settings
from ..db import Database, User
from .security import Cipher, hash_password, new_totp_secret, totp_uri


def _show_totp(secret: str, username: str) -> None:
    print("\nAdd this to your authenticator app (shown once, don't share or screenshot it):\n")
    print("  " + totp_uri(secret, username))
    print(f"\nOr enter the key manually: {secret}\n")
    try:
        import qrcode  # optional

        qr = qrcode.QRCode()
        qr.add_data(totp_uri(secret, username))
        qr.print_ascii(invert=True)
    except ImportError:
        print("(pip install qrcode to show a scannable QR code here)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="pari-auth")
    ap.add_argument("command", choices=["create-owner", "reset-totp"])
    ap.add_argument("--username", required=True)
    ap.add_argument("--display-name", default="MK")
    a = ap.parse_args(argv)

    cfg = get_settings()
    cfg.validate()
    database = Database(cfg.database_url)
    database.create_all()
    cipher = Cipher(cfg.data_key)

    with database.SessionLocal() as s:
        user = s.query(User).filter_by(username=a.username).one_or_none()
        if a.command == "create-owner":
            if s.query(User).count():
                print("An owner already exists. Pari is single-owner.", file=sys.stderr)
                return 1
            pw = getpass.getpass("New password (12+ characters): ")
            if pw != getpass.getpass("Repeat password: "):
                print("Passwords don't match.", file=sys.stderr)
                return 1
            secret = new_totp_secret()
            s.add(User(username=a.username, display_name=a.display_name, password_hash=hash_password(pw),
                       totp_secret_enc=cipher.encrypt(secret)))
            s.commit()
            audit.record(s, a.username, "owner_created", "cli")
        else:
            if user is None:
                print("No such user.", file=sys.stderr)
                return 1
            secret = new_totp_secret()
            user.totp_secret_enc = cipher.encrypt(secret)
            user.last_totp_step = 0
            s.commit()
            audit.record(s, a.username, "totp_reset", "cli")
        _show_totp(secret, a.username)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
