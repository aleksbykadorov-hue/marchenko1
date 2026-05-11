from fastapi.testclient import TestClient

from app.main import app


def test_register_login_me() -> None:
    with TestClient(app) as client:
        r = client.post("/auth/register", json={"email": "a@example.com", "password": "secret12"})
        assert r.status_code == 201, r.text
        user = r.json()
        assert user["email"] == "a@example.com"

        r = client.post("/auth/login", json={"email": "a@example.com", "password": "secret12"})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]

        r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        me = r.json()
        assert me["email"] == "a@example.com"

