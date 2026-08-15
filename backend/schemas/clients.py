"""Schemas Pydantic das rotas de clientes e reuniões."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, Field, PlainSerializer, field_validator

CompanySize = Literal["pme", "media", "enterprise"]
ClientStatus = Literal["prospect", "ativo", "inativo"]

_COMPANY_SIZE_ALIASES = {"pme": "pme", "media": "media", "enterprise": "enterprise"}
_BLANK_FIELDS = (
    "segment",
    "website",
    "city",
    "state",
    "contact_name",
    "contact_role",
    "contact_email",
    "contact_phone",
    "owner",
    "notes",
)


def _iso_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


UtcDateTime = Annotated[datetime, PlainSerializer(_iso_utc, return_type=str)]


def _blank_to_none(value: object) -> object:
    if not isinstance(value, str):
        return value
    cleaned = " ".join(value.split()).strip()
    return cleaned or None


def _normalize_company_size(value: object) -> object:
    cleaned = _blank_to_none(value)
    if not isinstance(cleaned, str):
        return cleaned
    key = cleaned.casefold().replace("é", "e")
    return _COMPANY_SIZE_ALIASES.get(key, cleaned)


def _normalize_status(value: object, *, empty_default: str | None) -> object:
    cleaned = _blank_to_none(value)
    if not isinstance(cleaned, str):
        return empty_default if cleaned is None else cleaned
    return cleaned.casefold()


class ClientSharedFields(BaseModel):
    segment: str | None = Field(default=None, max_length=120)
    company_size: CompanySize | None = None
    website: str | None = Field(default=None, max_length=300)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=2)
    contact_name: str | None = Field(default=None, max_length=200)
    contact_role: str | None = Field(default=None, max_length=120)
    contact_email: str | None = Field(default=None, max_length=200)
    contact_phone: str | None = Field(default=None, max_length=40)
    owner: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator(*_BLANK_FIELDS, mode="before")
    @classmethod
    def empty_to_none(cls, value: object) -> object:
        return _blank_to_none(value)

    @field_validator("state")
    @classmethod
    def uppercase_state(cls, value: str | None) -> str | None:
        return value.upper() if value else None

    @field_validator("company_size", mode="before")
    @classmethod
    def normalize_company_size(cls, value: object) -> object:
        return _normalize_company_size(value)


class ClientProfile(ClientSharedFields):
    status: ClientStatus = "prospect"

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: object) -> object:
        return _normalize_status(value, empty_default="prospect")


class ClientCreate(ClientProfile):
    name: str = Field(min_length=1, max_length=200)


class ClientUpdate(ClientSharedFields):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: ClientStatus | None = None

    @field_validator("name", mode="before")
    @classmethod
    def empty_name_to_none(cls, value: object) -> object:
        return _blank_to_none(value)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: object) -> object:
        return _normalize_status(value, empty_default=None)


class ClientListItem(ClientProfile):
    id: int
    name: str
    created_at: UtcDateTime
    meetings_count: int
    last_meeting_at: UtcDateTime | None = None


class MeetingSummary(BaseModel):
    id: int
    source_filename: str
    created_at: UtcDateTime
    conta: str
    status: str


class ClientDetail(ClientProfile):
    id: int
    name: str
    created_at: UtcDateTime
    meetings: list[MeetingSummary]


class MeetingDetail(BaseModel):
    id: int
    client_id: int
    client_name: str
    source_filename: str
    created_at: UtcDateTime
    triage: str
    selected_agents: list[str]
    final_report: dict
