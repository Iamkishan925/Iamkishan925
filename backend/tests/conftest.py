import pyotp
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from pari.auth.security import Cipher, hash_password, new_totp_secret
from pari.config import Settings
from pari.db import User
from pari.main import create_app

PASSWORD = "correct horse battery"


@pytest.fixture
def cfg(tmp_path):
    return Settings(env="test", database_url=f"sqlite:///{tmp_path}/t.db", data_key=Fernet.generate_key().decode(),
                    allowed_origins=["http://localhost:5173"])


@pytest.fixture
def app(cfg):
    return create_app(cfg)


@pytest.fixture
def owner(app, cfg):
    secret = new_totp_secret()
    with app.state.db.SessionLocal() as s:
        s.add(User(username="mk", password_hash=hash_password(PASSWORD),
                   totp_secret_enc=Cipher(cfg.data_key).encrypt(secret)))
        s.commit()
    return pyotp.TOTP(secret)


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def logged_in(client, owner):
    r = client.post("/api/auth/login", json={"username": "mk", "password": PASSWORD, "totp": owner.now()})
    assert r.status_code == 200, r.text
    return client
