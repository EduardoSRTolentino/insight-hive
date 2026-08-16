from __future__ import annotations

from collections.abc import Iterator

import pytest

from security import (
    INSECURE_APP_PASSWORD,
    INSECURE_JWT_SECRET_KEY,
    assert_secure_secrets,
    authenticate_user,
    decode_access_token,
)
from settings import get_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Iterator[None]:
    yield
    get_settings.cache_clear()


def test_wrong_password_is_rejected() -> None:
    assert authenticate_user("admin", "wrong") is False


def test_valid_credentials() -> None:
    settings = get_settings()
    assert authenticate_user(settings.app_username, settings.app_password) is True


def test_invalid_token_returns_none() -> None:
    assert decode_access_token("not-a-jwt") is None


def test_production_rejects_default_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_PASSWORD", INSECURE_APP_PASSWORD)
    monkeypatch.setenv("JWT_SECRET_KEY", INSECURE_JWT_SECRET_KEY)
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="APP_PASSWORD"):
            assert_secure_secrets()
    finally:
        get_settings.cache_clear()
