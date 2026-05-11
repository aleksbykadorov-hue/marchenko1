from fastapi.testclient import TestClient

from app.main import app


def test_notify_creates_record() -> None:
    with TestClient(app) as client:
        r = client.post("/notify", json={"type": "message_created", "payload": {"chat_id": 1}})
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["status"] == "queued"
        assert isinstance(body["id"], int)

