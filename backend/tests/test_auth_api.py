from __future__ import annotations

from fastapi.testclient import TestClient


def test_login_rejects_bad_password(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "nope"},
    )
    assert response.status_code == 401


def test_login_returns_token(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert auth_headers["Authorization"].startswith("Bearer ")


def test_clients_require_bearer(client: TestClient) -> None:
    response = client.get("/api/clients")
    assert response.status_code == 401
