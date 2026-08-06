"""Autenticação simples via JWT, com usuário/senha fixos em variáveis de ambiente.

Escopo intencionalmente básico: não há hashing de senha nem banco de dados de
usuários. As credenciais válidas vêm de `APP_USERNAME`/`APP_PASSWORD` no `.env`.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

APP_USERNAME = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "admin")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def authenticate_user(username: str, password: str) -> bool:
    """Verifica se as credenciais informadas correspondem às fixas no .env."""
    return username == APP_USERNAME and password == APP_PASSWORD


def create_access_token(username: str) -> str:
    """Gera um token JWT assinado, contendo o usuário e a expiração."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """Decodifica o token JWT e retorna o usuário (`sub`), ou None se inválido/expirado."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
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
