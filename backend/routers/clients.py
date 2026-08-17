"""Rotas de clientes e reuniões persistidas."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import get_db
from models import Client, Meeting, User
from ownership import get_owned_client, get_owned_meeting
from schemas.clients import (
    ClientCreate,
    ClientDetail,
    ClientListItem,
    ClientUpdate,
    MeetingDetail,
    MeetingSummary,
)
from security import get_current_user

router = APIRouter(tags=["clients"])

DEFAULT_CONTA = "Não identificado"
DEFAULT_STATUS = "Pendente revisão humana"
PROFILE_FIELDS = (
    "segment",
    "company_size",
    "website",
    "city",
    "state",
    "contact_name",
    "contact_role",
    "contact_email",
    "contact_phone",
    "owner",
    "status",
    "notes",
)


def normalize_client_name(raw: str) -> str:
    return " ".join(raw.split()).strip()


def client_profile_data(client: Client) -> dict:
    return {
        "segment": client.segment,
        "company_size": client.company_size,
        "website": client.website,
        "city": client.city,
        "state": client.state,
        "contact_name": client.contact_name,
        "contact_role": client.contact_role,
        "contact_email": client.contact_email,
        "contact_phone": client.contact_phone,
        "owner": client.owner,
        "status": client.status or "prospect",
        "notes": client.notes,
    }


def to_list_item(
    client: Client,
    meetings_count: int = 0,
    last_meeting_at=None,
) -> ClientListItem:
    return ClientListItem(
        id=client.id,
        name=client.name,
        created_at=client.created_at,
        meetings_count=meetings_count,
        last_meeting_at=last_meeting_at,
        **client_profile_data(client),
    )


def apply_client_fields(client: Client, data: dict) -> None:
    if "name" in data and data["name"]:
        name = normalize_client_name(data["name"])
        if not name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Informe o nome do cliente.",
            )
        client.name = name
        client.name_key = name.casefold()
    for field in PROFILE_FIELDS:
        if field not in data:
            continue
        value = data[field]
        if field == "status" and not value:
            value = "prospect"
        setattr(client, field, value)


def meeting_summary(meeting: Meeting) -> MeetingSummary:
    report = meeting.final_report if isinstance(meeting.final_report, dict) else {}
    return MeetingSummary(
        id=meeting.id,
        source_filename=meeting.source_filename,
        created_at=meeting.created_at,
        conta=str(report.get("conta") or DEFAULT_CONTA),
        status=str(report.get("status") or DEFAULT_STATUS),
    )


def meeting_detail(meeting: Meeting) -> MeetingDetail:
    agents = meeting.selected_agents if isinstance(meeting.selected_agents, list) else []
    report = meeting.final_report if isinstance(meeting.final_report, dict) else {}
    return MeetingDetail(
        id=meeting.id,
        client_id=meeting.client_id,
        client_name=meeting.client.name,
        source_filename=meeting.source_filename,
        created_at=meeting.created_at,
        triage=meeting.triage,
        selected_agents=[str(item) for item in agents],
        final_report=report,
    )


@router.get("/clients", response_model=list[ClientListItem])
def list_clients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ClientListItem]:
    rows = db.execute(
        select(
            Client,
            func.count(Meeting.id).label("meetings_count"),
            func.max(Meeting.created_at).label("last_meeting_at"),
        )
        .outerjoin(Meeting)
        .where(Client.user_id == current_user.id)
        .group_by(Client.id)
        .order_by(func.max(Meeting.created_at).desc(), Client.name)
    ).all()

    return [
        to_list_item(client, int(meetings_count or 0), last_meeting_at)
        for client, meetings_count, last_meeting_at in rows
    ]


@router.post("/clients", response_model=ClientListItem, status_code=status.HTTP_201_CREATED)
def create_client(
    body: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClientListItem:
    name = normalize_client_name(body.name)
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe o nome do cliente.",
        )

    payload = body.model_dump()
    payload.pop("name")
    client = Client(
        name=name,
        name_key=name.casefold(),
        user_id=current_user.id,
        **payload,
    )
    db.add(client)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um cliente com esse nome.",
        ) from exc
    db.refresh(client)
    return to_list_item(client)


@router.patch("/clients/{client_id}", response_model=ClientDetail)
def update_client(
    client_id: int,
    body: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClientDetail:
    client = get_owned_client(db, current_user, client_id)

    apply_client_fields(client, body.model_dump(exclude_unset=True))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um cliente com esse nome.",
        ) from exc
    db.refresh(client)

    meetings = db.scalars(
        select(Meeting)
        .where(Meeting.client_id == client_id)
        .order_by(Meeting.created_at.desc())
    ).all()
    return ClientDetail(
        id=client.id,
        name=client.name,
        created_at=client.created_at,
        meetings=[meeting_summary(item) for item in meetings],
        **client_profile_data(client),
    )


@router.get("/clients/{client_id}", response_model=ClientDetail)
def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClientDetail:
    client = get_owned_client(db, current_user, client_id)

    meetings = db.scalars(
        select(Meeting)
        .where(Meeting.client_id == client_id)
        .order_by(Meeting.created_at.desc())
    ).all()

    return ClientDetail(
        id=client.id,
        name=client.name,
        created_at=client.created_at,
        meetings=[meeting_summary(item) for item in meetings],
        **client_profile_data(client),
    )


@router.get("/meetings/{meeting_id}", response_model=MeetingDetail)
def get_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeetingDetail:
    meeting = get_owned_meeting(db, current_user, meeting_id)
    return meeting_detail(meeting)


@router.delete("/meetings/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    meeting = get_owned_meeting(db, current_user, meeting_id)
    db.delete(meeting)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
