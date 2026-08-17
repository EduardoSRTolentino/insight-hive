from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ratelimit import auth_limiter
from security import bootstrap_admin_email
from settings import get_settings


def test_login_rejects_bad_password(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        data={"username": bootstrap_admin_email(), "password": "nope"},
    )
    assert response.status_code == 401


def test_login_returns_token(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert auth_headers["Authorization"].startswith("Bearer ")


def test_register_and_me(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Ana Silva",
            "email": "ana@example.com",
            "password": "password12",
            "company": "TOTVS",
            "job_title": "CS",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    token = body["access_token"]
    assert body["user"]["email"] == "ana@example.com"
    assert body["user"]["full_name"] == "Ana Silva"
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "ana@example.com"
    assert body["full_name"] == "Ana Silva"
    assert body["company"] == "TOTVS"
    assert body["job_title"] == "CS"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    payload = {
        "full_name": "Ana Silva",
        "email": "dup@example.com",
        "password": "password12",
    }
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 200
    second = client.post("/api/auth/register", json=payload)
    assert second.status_code == 409


def test_register_normalizes_email(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Ana",
            "email": "  Ana.Case@Example.COM ",
            "password": "password12",
        },
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.json()["email"] == "ana.case@example.com"

    login = client.post(
        "/api/auth/login",
        data={"username": "Ana.Case@Example.COM", "password": "password12"},
    )
    assert login.status_code == 200


def test_patch_me(client: TestClient, make_user_headers) -> None:
    headers = make_user_headers(email="patch@example.com")
    updated = client.patch(
        "/api/auth/me",
        json={"city": "São Paulo", "state": "sp", "job_title": "AE"},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["city"] == "São Paulo"
    assert body["state"] == "SP"
    assert body["job_title"] == "AE"


def test_clients_require_bearer(client: TestClient) -> None:
    response = client.get("/api/clients")
    assert response.status_code == 401


def test_register_disabled(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_REGISTRATION", "0")
    get_settings.cache_clear()
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Ana Silva",
            "email": "blocked@example.com",
            "password": "password12",
        },
    )
    assert response.status_code == 403
    assert "desativado" in response.json()["detail"]


def test_register_off_by_default_in_production(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ALLOW_REGISTRATION", "")
    get_settings.cache_clear()
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Ana Silva",
            "email": "prod@example.com",
            "password": "password12",
        },
    )
    assert response.status_code == 403


def test_auth_rate_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_RATE_LIMIT", "2")
    get_settings.cache_clear()
    auth_limiter.clear()
    payload = {"full_name": "Ana", "password": "password12"}
    assert (
        client.post(
            "/api/auth/register", json={**payload, "email": "rate1@example.com"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/auth/register", json={**payload, "email": "rate2@example.com"}
        ).status_code
        == 200
    )
    third = client.post(
        "/api/auth/register", json={**payload, "email": "rate3@example.com"}
    )
    assert third.status_code == 429
    assert "Retry-After" in third.headers
    auth_limiter.clear()
