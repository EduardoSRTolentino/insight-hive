from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from security import (
    INSECURE_APP_PASSWORD,
    INSECURE_JWT_SECRET_KEY,
    JWT_ALGORITHM,
    assert_secure_admin_seed,
    assert_secure_secrets,
    bootstrap_admin_email,
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


def test_expired_token_returns_none() -> None:
    settings = get_settings()
    payload = {
        "sub": "1",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)
    assert decode_access_token(token) is None


def test_token_signed_with_wrong_secret_returns_none() -> None:
    payload = {
        "sub": "1",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    token = jwt.encode(payload, "a-completely-different-secret", algorithm=JWT_ALGORITHM)
    assert decode_access_token(token) is None


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


def test_production_rejects_short_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_PASSWORD", "a-strong-password-not-the-default")
    monkeypatch.setenv("JWT_SECRET_KEY", "short-secret")
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="menos de 32"):
            assert_secure_secrets()
    finally:
        get_settings.cache_clear()


def test_assert_secure_admin_seed_passes_with_strong_password(client: TestClient) -> None:
    # O fixture `client` já subiu a app (lifespan) com APP_PASSWORD de teste,
    # que não é o default inseguro — não deve levantar.
    from db import SessionLocal

    with SessionLocal() as db:
        assert_secure_admin_seed(db)


def _with_admin_hash_swapped(new_hash: str):
    """Troca o password_hash do admin semeado e devolve uma função que
    restaura o valor original — o banco de teste é compartilhado entre
    testes na sessão, então mexer nele sem desfazer quebraria outros testes
    (ex.: o fixture `auth_headers`, que loga com a senha de `.env` de teste)."""
    from db import SessionLocal
    from models import User

    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.email == bootstrap_admin_email()))
        assert admin is not None
        original_hash = admin.password_hash
        admin.password_hash = new_hash
        db.commit()

    def _restore() -> None:
        with SessionLocal() as db:
            admin = db.scalar(select(User).where(User.email == bootstrap_admin_email()))
            assert admin is not None
            admin.password_hash = original_hash
            db.commit()

    return _restore


def test_assert_secure_admin_seed_rejects_stale_insecure_hash_in_prod(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Simula o cenário real do achado: o admin foi semeado (na migração) com
    # a senha insegura, e o env foi trocado depois — mas o hash já gravado no
    # banco continua sendo o antigo. Mudar APP_PASSWORD sozinho não corrige.
    from db import SessionLocal

    restore = _with_admin_hash_swapped(hash_password(INSECURE_APP_PASSWORD))
    monkeypatch.setenv("APP_PASSWORD", "uma-senha-bem-diferente-agora")
    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()
    try:
        with SessionLocal() as db:
            with pytest.raises(RuntimeError, match="senha insegura"):
                assert_secure_admin_seed(db)
    finally:
        get_settings.cache_clear()
        restore()


def test_assert_secure_admin_seed_only_warns_in_development(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from db import SessionLocal

    restore = _with_admin_hash_swapped(hash_password(INSECURE_APP_PASSWORD))
    monkeypatch.setenv("APP_ENV", "development")
    get_settings.cache_clear()
    try:
        with SessionLocal() as db:
            assert_secure_admin_seed(db)  # não levanta em dev, só avisa
    finally:
        get_settings.cache_clear()
        restore()
