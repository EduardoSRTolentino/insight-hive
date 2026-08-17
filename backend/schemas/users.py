"""Schemas Pydantic das rotas de autenticação e perfil."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from emails import is_valid_email, normalize_email
from schemas.clients import UtcDateTime, _blank_to_none

_BLANK_FIELDS = (
    "company",
    "job_title",
    "department",
    "phone",
    "city",
    "state",
    "linkedin_url",
    "bio",
)


class UserSharedFields(BaseModel):
    company: str | None = Field(default=None, max_length=200)
    job_title: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=2)
    linkedin_url: str | None = Field(default=None, max_length=300)
    bio: str | None = Field(default=None, max_length=4000)

    @field_validator(*_BLANK_FIELDS, mode="before")
    @classmethod
    def empty_to_none(cls, value: object) -> object:
        return _blank_to_none(value)

    @field_validator("state")
    @classmethod
    def uppercase_state(cls, value: str | None) -> str | None:
        return value.upper() if value else None


class UserRegister(UserSharedFields):
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        cleaned = _blank_to_none(value)
        return cleaned if cleaned is not None else value

    @field_validator("email")
    @classmethod
    def normalize_and_check_email(cls, value: str) -> str:
        email = normalize_email(value)
        if not is_valid_email(email):
            raise ValueError("Informe um e-mail válido.")
        return email


class UserUpdate(UserSharedFields):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, min_length=3, max_length=200)

    @field_validator("full_name", mode="before")
    @classmethod
    def empty_name_to_none(cls, value: object) -> object:
        return _blank_to_none(value)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_optional_email(cls, value: object) -> object:
        cleaned = _blank_to_none(value)
        if not isinstance(cleaned, str):
            return cleaned
        email = normalize_email(cleaned)
        if not is_valid_email(email):
            raise ValueError("Informe um e-mail válido.")
        return email


class UserPublic(UserSharedFields):
    id: int
    email: str
    full_name: str
    created_at: UtcDateTime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
