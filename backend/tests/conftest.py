"""Ambiente de teste: SQLite temporário e settings antes de importar a API."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

_DB_PATH = Path(tempfile.mkdtemp()) / "pytest.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH.as_posix()}"
os.environ["APP_ENV"] = "development"
os.environ["APP_USERNAME"] = "admin"
os.environ["APP_PASSWORD"] = "test-password"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-32bytes-long!"
os.environ["MAX_UPLOAD_BYTES"] = "2048"
os.environ["AUTH_RATE_LIMIT"] = "0"

from settings import get_settings  # noqa: E402

get_settings.cache_clear()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from api import app  # noqa: E402
from security import bootstrap_admin_email  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        data={
            "username": bootstrap_admin_email(),
            "password": os.environ["APP_PASSWORD"],
        },
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def register_headers(client: TestClient, **overrides: object) -> dict[str, str]:
    payload: dict[str, object] = {
        "full_name": "Usuária Teste",
        "email": f"user-{uuid4().hex[:8]}@example.com",
        "password": "password12",
        **overrides,
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_user_headers(client: TestClient):
    def _make(**overrides: object) -> dict[str, str]:
        return register_headers(client, **overrides)

    return _make
