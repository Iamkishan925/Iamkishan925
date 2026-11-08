"""FastAPI app. Run locally with: uvicorn pari.main:app --reload"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .api import system
from .auth import routes as auth_routes
from .auth.ratelimit import LoginLimiter
from .auth.security import Cipher
from .config import Settings, get_settings
from .db import Database

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def create_app(cfg: Settings | None = None) -> FastAPI:
    cfg = cfg or get_settings()
    cfg.validate()

    app = FastAPI(title="Pari", docs_url=None if cfg.is_production else "/api/docs", redoc_url=None,
                  openapi_url=None if cfg.is_production else "/api/openapi.json")
    app.state.settings = cfg
    app.state.db = Database(cfg.database_url)
    app.state.db.create_all()
    app.state.cipher = Cipher(cfg.data_key)
    app.state.login_limiter = LoginLimiter(cfg.login_max_failures, cfg.login_lockout_minutes * 60)

    @app.middleware("http")
    async def security(request: Request, call_next):
        # CSRF defence in depth on top of SameSite=Strict cookies: a browser always sends
        # Origin on cross-site POSTs, so reject any state-changing request from a foreign origin.
        origin = request.headers.get("origin")
        if request.method in UNSAFE_METHODS and origin and origin not in cfg.allowed_origins:
            return JSONResponse({"detail": "origin not allowed"}, status_code=403)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cache-Control", "no-store")
        return response

    app.include_router(system.router)
    app.include_router(auth_routes.router)
    return app


def __getattr__(name: str):
    # `uvicorn pari.main:app` builds the app lazily so importing this module in tests has no side effects.
    if name == "app":
        return create_app()
    raise AttributeError(name)
