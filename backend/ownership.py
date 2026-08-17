"""Acesso a clientes e reuniões restrito ao dono."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import AnalysisJob, Client, Meeting, User


def get_owned_client(db: Session, user: User, client_id: int) -> Client:
    client = db.scalar(
        select(Client).where(Client.id == client_id, Client.user_id == user.id)
    )
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado.",
        )
    return client


def get_owned_meeting(db: Session, user: User, meeting_id: int) -> Meeting:
    meeting = db.scalar(
        select(Meeting)
        .join(Client)
        .where(Meeting.id == meeting_id, Client.user_id == user.id)
    )
    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reunião não encontrada.",
        )
    return meeting


def get_owned_job(db: Session, user: User, job_id: int) -> AnalysisJob:
    job = db.scalar(
        select(AnalysisJob).where(AnalysisJob.id == job_id, AnalysisJob.user_id == user.id)
    )
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Análise não encontrada.",
        )
    return job
