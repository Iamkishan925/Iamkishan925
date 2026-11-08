def test_health_is_public_and_minimal(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["database"] == "ok"
    assert r.headers["x-frame-options"] == "DENY"


def test_status_and_audit_need_login(client):
    assert client.get("/api/status").status_code == 401
    assert client.get("/api/audit").status_code == 401


def test_status_reports_live_trading_off(logged_in):
    body = logged_in.get("/api/status").json()
    assert body["live_trading"] is False
    states = {m["name"]: m["state"] for m in body["modules"]}
    assert states["execution"] == "disabled" and states["auth"] == "ready"


def test_audit_shows_login(logged_in):
    actions = [e["action"] for e in logged_in.get("/api/audit").json()]
    assert "login" in actions
