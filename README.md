# Pari

MK's personal multilingual AI companion and trading-intelligence platform. It is built in
phases (see [docs/architecture.md](docs/architecture.md)).

**Current state: Phase 2.** Working now:
- owner login (password + authenticator code), device sessions and an activity log
- a startup animation and an original animated Pari avatar (idle, listening, thinking and speaking states)
- chat with saved conversations, a live microphone waveform (mic test only), and security notifications
- Gujarati/English, dark/light, desktop sidebar and mobile bottom navigation

**AI replies, speech-to-text and Pari's voice are Phase 3.** Until then chat stores your messages
and says plainly that the AI isn't connected. It never makes up a reply. Market data and trading
are later phases, and real-money trading is disabled.

## Layout

```
backend/    FastAPI app (Python 3.12)   pari/auth, pari/api, pari/audit.py, pari/db.py
frontend/   React + TypeScript + Vite + Tailwind PWA, plus the production Caddyfile
infra/      docker-compose.yml (Caddy + backend + PostgreSQL)
docs/       architecture and phase plan
```

## Run locally

You need Python 3.12+ and Node 22+. Run each block from the repo root.

1. Install the backend:

```bash
cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
```

2. Create a data-encryption key and keep a copy in your password manager:

```bash
export PARI_DATA_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

3. Create the owner account. It asks for your password without showing it, then prints a
   QR/URI for your authenticator app:

```bash
python -m pari.auth.cli create-owner --username mk
```

4. Start the backend:

```bash
uvicorn pari.main:app --reload
```

5. In a second terminal, start the frontend and open http://localhost:5173:

```bash
cd frontend && npm install && npm run dev
```

Tests:

```bash
cd backend && pytest -q
```

## Deploy (UK VPS or any Linux server)

1. Point a DNS name at the server. Open only ports 80 and 443.
2. Copy `.env.example` to `.env` and set `PARI_DATA_KEY`, `POSTGRES_PASSWORD` and `PARI_DOMAIN`.
3. Start the stack:

```bash
docker compose -f infra/docker-compose.yml --env-file .env up -d --build
```

4. Create the owner inside the container:

```bash
docker compose -f infra/docker-compose.yml --env-file .env exec backend python -m pari.auth.cli create-owner --username mk
```

Caddy gets a Let's Encrypt certificate automatically. Only Caddy is exposed; the backend and
PostgreSQL stay on the internal Docker network.

> The Docker setup is written but has not been run end-to-end yet. The build environment had
> no Docker daemon. The backend and frontend were tested directly.

## Security notes

- Passwords are hashed with Argon2id. TOTP secrets are encrypted with `PARI_DATA_KEY`. A used
  TOTP code cannot be replayed.
- The session cookie is `HttpOnly`, `SameSite=Strict`, and `Secure` in production. Only a
  SHA-256 hash of the session token is stored.
- Sessions expire after 12 h idle or 7 days. You can sign any device out from the dashboard.
- Logins lock for 15 minutes after 5 failures per username or IP. Error messages don't reveal
  whether the username or the password was wrong.
- State-changing requests from foreign origins are rejected. Security headers and a CSP are set.
- Every login, failure, logout and session revocation is in the audit log. Secrets are
  redacted.
- `.env` is gitignored. CI runs a gitleaks secret scan.
