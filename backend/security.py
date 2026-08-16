"""Autenticação simples via JWT, com usuário/senha fixos em variáveis de ambiente.

Escopo intencionalmente básico: não há hashing de senha nem banco de dados de
usuários. As credenciais válidas vêm de `APP_USERNAME`/`APP_PASSWORD` no `.env`.
"""

import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from settings import get_settings

logger = logging.getLogger(__name__)

INSECURE_APP_PASSWORD = "admin"
INSECURE_JWT_SECRET_KEY = "change-this-secret-key"
JWT_ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def assert_secure_secrets() -> None:
    """Recusa defaults inseguros em produção; em development só avisa."""
    settings = get_settings()
    using_defaults = (
        settings.app_password == INSECURE_APP_PASSWORD
        or settings.jwt_secret_key == INSECURE_JWT_SECRET_KEY
    )
    if not using_defaults:
        return

    message = (
        "Secrets inseguros detectados. Preencha APP_PASSWORD e JWT_SECRET_KEY no .env."
    )
    if settings.app_env.lower() in ("production", "prod"):
        raise RuntimeError(message)
    logger.warning(message)


def authenticate_user(username: str, password: str) -> bool:
    """Verifica se as credenciais informadas correspondem às fixas no `.env`."""
    settings = get_settings()
    user_ok = hmac.compare_digest(username, settings.app_username)
    password_ok = hmac.compare_digest(password, settings.app_password)
    return user_ok and password_ok


def create_access_token(username: str) -> str:
    """Gera um token JWT assinado, contendo o usuário e a expiração."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """Decodifica o token JWT e retorna o usuário (`sub`), ou None se inválido/expirado."""
    try:
        payload = jwt.decode(
            token, get_settings().jwt_secret_key, algorithms=[JWT_ALGORITHM]
        )
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Dependência do FastAPI que protege rotas exigindo um token JWT válido."""
    username = decode_access_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou token expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username
