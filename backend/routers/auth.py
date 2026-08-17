"""Rotas de autenticação: cadastro, login e perfil."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import get_db
from models import User
from ratelimit import enforce_auth_rate_limit
from schemas.users import TokenResponse, UserPublic, UserRegister, UserUpdate
from security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
)
from settings import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

PROFILE_FIELDS = (
    "company",
    "job_title",
    "department",
    "phone",
    "city",
    "state",
    "linkedin_url",
    "bio",
)


def to_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
        company=user.company,
        job_title=user.job_title,
        department=user.department,
        phone=user.phone,
        city=user.city,
        state=user.state,
        linkedin_url=user.linkedin_url,
        bio=user.bio,
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    dependencies=[Depends(enforce_auth_rate_limit)],
)
def register(body: UserRegister, db: Session = Depends(get_db)) -> TokenResponse:
    if not get_settings().registration_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cadastro de novas contas está desativado.",
        )
    payload = body.model_dump()
    password = payload.pop("password")
    user = User(password_hash=hash_password(password), **payload)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta com esse e-mail.",
        ) from exc
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id), user=to_public(user))


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(enforce_auth_rate_limit)],
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(user.id), user=to_public(user))


@router.get("/me", response_model=UserPublic)
def read_me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return to_public(current_user)


@router.patch("/me", response_model=UserPublic)
def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPublic:
    data = body.model_dump(exclude_unset=True)
    if "full_name" in data and data["full_name"]:
        current_user.full_name = data["full_name"]
    if "email" in data and data["email"]:
        current_user.email = data["email"]
    for field in PROFILE_FIELDS:
        if field in data:
            setattr(current_user, field, data[field])
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta com esse e-mail.",
        ) from exc
    db.refresh(current_user)
    return to_public(current_user)
