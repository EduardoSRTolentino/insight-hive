"""Ambiente de teste: SQLite temporário e settings antes de importar a API."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

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

from settings import get_settings  # noqa: E402

get_settings.cache_clear()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from api import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        data={
            "username": os.environ["APP_USERNAME"],
            "password": os.environ["APP_PASSWORD"],
        },
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
