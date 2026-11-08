from pari.auth.security import hash_password
from pari.db import User


def _conv(c):
    return c.post("/api/chat/conversations", json={}).json()["id"]


def test_chat_requires_login(client):
    assert client.get("/api/chat/conversations").status_code == 401


def test_message_saved_and_no_fake_reply(logged_in):
    cid = _conv(logged_in)
    r = logged_in.post(f"/api/chat/conversations/{cid}/messages", json={"content": "  કેમ છો Pari?  "}).json()
    assert r["reply"] is None and r["notice"] == "ai_not_configured"
    msgs = logged_in.get(f"/api/chat/conversations/{cid}/messages").json()
    assert [(m["role"], m["content"]) for m in msgs] == [("user", "કેમ છો Pari?")]
    conv = logged_in.get("/api/chat/conversations").json()[0]
    assert conv["title"] == "કેમ છો Pari?"


def test_assistant_hook_used_when_configured(app, logged_in):
    class Echo:
        def reply(self, history):
            return f"{len(history)} messages"

    app.state.assistant = Echo()
    cid = _conv(logged_in)
    r = logged_in.post(f"/api/chat/conversations/{cid}/messages", json={"content": "hi"}).json()
    assert r["reply"]["content"] == "1 messages" and r["reply"]["role"] == "assistant"


def test_validation_and_delete(logged_in):
    cid = _conv(logged_in)
    assert logged_in.post(f"/api/chat/conversations/{cid}/messages", json={"content": ""}).status_code == 422
    assert logged_in.post(f"/api/chat/conversations/{cid}/messages", json={"content": "x" * 8001}).status_code == 422
    assert logged_in.delete(f"/api/chat/conversations/{cid}").status_code == 200
    assert logged_in.get(f"/api/chat/conversations/{cid}/messages").status_code == 404


def test_cannot_read_other_users_conversation(app, logged_in):
    with app.state.db.SessionLocal() as s:
        other = User(username="other", password_hash=hash_password("another long password"), totp_secret_enc="x")
        s.add(other)
        s.commit()
        from pari.db import Conversation
        conv = Conversation(user_id=other.id, title="private")
        s.add(conv)
        s.commit()
        cid = conv.id
    assert logged_in.get(f"/api/chat/conversations/{cid}/messages").status_code == 404
    assert all(c["id"] != cid for c in logged_in.get("/api/chat/conversations").json())
