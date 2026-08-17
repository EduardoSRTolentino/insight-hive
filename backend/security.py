"""Autenticação JWT com usuários persistidos e senha com hash."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from db import get_db
from emails import normalize_email
from models import User
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


def bootstrap_admin_email(username: str | None = None) -> str:
    """E-mail do admin seed: o username do env se já for e-mail, senão `{user}@insight-hive.local`."""
    raw = (username if username is not None else get_settings().app_username).strip()
    if "@" in raw:
        return normalize_email(raw)
    return f"{normalize_email(raw)}@insight-hive.local"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("ascii"),
        )
    except (ValueError, TypeError):
        return False


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Localiza o usuário pelo e-mail e verifica a senha."""
    normalized = normalize_email(email)
    user = db.scalar(select(User).where(User.email == normalized))
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(user_id: int) -> str:
    """Gera um token JWT assinado, contendo o id do usuário e a expiração."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """Decodifica o token JWT e retorna o `sub`, ou None se inválido/expirado."""
    try:
        payload = jwt.decode(
            token, get_settings().jwt_secret_key, algorithms=[JWT_ALGORITHM]
        )
        subject = payload.get("sub")
        if isinstance(subject, int):
            return str(subject)
        return subject if isinstance(subject, str) and subject else None
    except jwt.PyJWTError:
        return None


def user_id_from_token(token: str) -> int:
    """Extrai o id do usuário do JWT ou responde 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    subject = decode_access_token(token)
    if subject is None:
        raise credentials_exception
    try:
        return int(subject)
    except (TypeError, ValueError):
        raise credentials_exception from None


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """Dependência que só decodifica o JWT — não abre sessão no banco."""
    return user_id_from_token(token)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependência do FastAPI que protege rotas exigindo um token JWT válido."""
    user = db.get(User, user_id_from_token(token))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou token expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
