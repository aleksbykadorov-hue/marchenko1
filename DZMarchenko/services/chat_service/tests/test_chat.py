from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.settings import settings


def _make_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def test_chat_crud_flow() -> None:
    with TestClient(app) as client:
        token = _make_token(1)

        r = client.post("/chats", json={"title": "Group 1"}, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 201, r.text
        chat_id = r.json()["id"]

        r = client.get("/chats", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        assert any(c["id"] == chat_id for c in r.json())

        r = client.post(
            f"/chats/{chat_id}/members",
            json={"user_id": 2, "role": "member"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 204, r.text

        r = client.post(
            f"/chats/{chat_id}/messages",
            json={"text": "hello"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201, r.text
        msg_id = r.json()["id"]

        r = client.get(f"/chats/{chat_id}/messages", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        assert any(m["id"] == msg_id for m in r.json())

        r = client.delete(f"/messages/{msg_id}", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 204, r.text

