from __future__ import annotations

from collections.abc import Iterator

import pytest

from security import (
    INSECURE_APP_PASSWORD,
    INSECURE_JWT_SECRET_KEY,
    assert_secure_secrets,
    create_access_token,
    decode_access_token,
    hash_password,
    user_id_from_token,
    verify_password,
)
from settings import get_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Iterator[None]:
    yield
    get_settings.cache_clear()


def test_hash_and_verify_password() -> None:
    hashed = hash_password("secret-pass")
    assert hashed != "secret-pass"
    assert verify_password("secret-pass", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token() -> None:
    token = create_access_token(42)
    assert decode_access_token(token) == "42"


def test_invalid_token_returns_none() -> None:
    assert decode_access_token("not-a-jwt") is None


def test_user_id_from_token() -> None:
    token = create_access_token(7)
    assert user_id_from_token(token) == 7


def test_user_id_from_invalid_token() -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        user_id_from_token("not-a-jwt")
    assert exc.value.status_code == 401


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
