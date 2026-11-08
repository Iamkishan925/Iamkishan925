"""Web API so MK can talk to Pari from phone or laptop.

Run: uvicorn mk_pari.app:app --host 0.0.0.0 --port 8000
Every request needs `Authorization: Bearer $PARI_API_TOKEN`. Put HTTPS in front
(Caddy, nginx, or a cloud load balancer) before exposing it to the internet.
"""

from __future__ import annotations

import hmac

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from . import tts
from .agent import PariAgent
from .config import load_settings

settings = load_settings()
app = FastAPI(title="MK-Pari")
_agent: PariAgent | None = None


def agent() -> PariAgent:
    global _agent
    if _agent is None:
        _agent = PariAgent(settings)
    return _agent


def auth(authorization: str = Header("")) -> None:
    if not settings.api_token:
        raise HTTPException(503, "PARI_API_TOKEN is not set on the server")
    if not hmac.compare_digest(authorization, f"Bearer {settings.api_token}"):
        raise HTTPException(401, "bad token")


class AskIn(BaseModel):
    symbol: str
    question: str = "Analyse this and tell me if there is a trade."
    news_tickers: list[str] | None = None
    language: str | None = None


class SpeakIn(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"ok": True, "mode": "LIVE" if settings.is_live else "paper", "broker": settings.broker}


@app.post("/ask", dependencies=[Depends(auth)])
def ask(body: AskIn):
    r = agent().ask(body.symbol, body.question, body.news_tickers, body.language)
    return {
        "as_of": r.as_of,
        "view": r.view.model_dump(),
        "risk": r.risk_reasons,
        "proposal_id": r.proposal.id if r.proposal and not r.executed else None,
        "quantity": r.proposal.decision.quantity if r.proposal else None,
        "executed": r.executed,
    }


@app.post("/confirm/{proposal_id}", dependencies=[Depends(auth)])
def confirm(proposal_id: str):
    try:
        return agent().confirm(proposal_id)
    except KeyError:
        raise HTTPException(404, "no such pending proposal")
    except TimeoutError as e:
        raise HTTPException(409, str(e))


@app.post("/reject/{proposal_id}", dependencies=[Depends(auth)])
def reject(proposal_id: str):
    agent().reject(proposal_id)
    return {"ok": True}


@app.post("/speak", dependencies=[Depends(auth)])
def speak(body: SpeakIn):
    audio = tts.speak(body.text, settings.elevenlabs_key, settings.elevenlabs_voice_id)
    if audio is None:
        raise HTTPException(503, "TTS not configured (ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID)")
    return Response(audio, media_type="audio/mpeg")
