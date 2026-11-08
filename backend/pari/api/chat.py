"""Conversation storage. The AI reply is plugged in through `app.state.assistant` (Phase 3).

Until an assistant is configured, sending a message stores it and returns
`reply: null` with `notice: "ai_not_configured"` - Pari never fakes an answer.
"""

from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import Conversation, Message, User, utcnow
from ..deps import current_user, db

router = APIRouter(prefix="/api/chat", tags=["chat"])

MAX_MESSAGE_CHARS = 8000


class Assistant(Protocol):
    def reply(self, history: list[dict]) -> str: ...


class NewConversation(BaseModel):
    title: str = Field("", max_length=120)


class NewMessage(BaseModel):
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


def _conv_out(c: Conversation) -> dict:
    return {"id": c.id, "title": c.title, "created_at": c.created_at, "updated_at": c.updated_at}


def _msg_out(m: Message) -> dict:
    return {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at}


def _own(s: Session, user: User, conv_id: int) -> Conversation:
    conv = s.get(Conversation, conv_id)
    if conv is None or conv.user_id != user.id:  # 404 either way: don't reveal other ids
        raise HTTPException(404, "no such conversation")
    return conv


@router.get("/conversations")
def list_conversations(user: User = Depends(current_user), s: Session = Depends(db)):
    rows = (s.query(Conversation).filter_by(user_id=user.id)
            .order_by(Conversation.updated_at.desc()).limit(200).all())
    return [_conv_out(c) for c in rows]


@router.post("/conversations")
def create_conversation(body: NewConversation, user: User = Depends(current_user), s: Session = Depends(db)):
    conv = Conversation(user_id=user.id, title=body.title.strip())
    s.add(conv)
    s.commit()
    return _conv_out(conv)


@router.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: int, user: User = Depends(current_user), s: Session = Depends(db)):
    conv = _own(s, user, conv_id)
    s.query(Message).filter_by(conversation_id=conv.id).delete()
    s.delete(conv)
    s.commit()
    return {"ok": True}


@router.get("/conversations/{conv_id}/messages")
def list_messages(conv_id: int, user: User = Depends(current_user), s: Session = Depends(db)):
    conv = _own(s, user, conv_id)
    rows = s.query(Message).filter_by(conversation_id=conv.id).order_by(Message.id).all()
    return [_msg_out(m) for m in rows]


@router.post("/conversations/{conv_id}/messages")
def send_message(conv_id: int, body: NewMessage, request: Request, user: User = Depends(current_user),
                 s: Session = Depends(db)):
    conv = _own(s, user, conv_id)
    text = body.content.strip()
    if not text:
        raise HTTPException(422, "empty message")
    msg = Message(conversation_id=conv.id, role="user", content=text)
    s.add(msg)
    if not conv.title:
        conv.title = text[:60]
    conv.updated_at = utcnow()
    s.commit()

    assistant: Assistant | None = getattr(request.app.state, "assistant", None)
    if assistant is None:
        return {"message": _msg_out(msg), "reply": None, "notice": "ai_not_configured"}

    history = [{"role": m.role, "content": m.content}
               for m in s.query(Message).filter_by(conversation_id=conv.id).order_by(Message.id)]
    reply = Message(conversation_id=conv.id, role="assistant", content=assistant.reply(history))
    s.add(reply)
    s.commit()
    return {"message": _msg_out(msg), "reply": _msg_out(reply), "notice": None}
