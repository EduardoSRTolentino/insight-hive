"""Modelos persistidos: usuário, cliente e reunião (análise)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    clients: Mapped[list[Client]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    analysis_jobs: Mapped[list["AnalysisJob"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (
        UniqueConstraint("user_id", "name_key", name="uq_clients_user_id_name_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_key: Mapped[str] = mapped_column(String(200), nullable=False)
    segment: Mapped[str | None] = mapped_column(String(120), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(40), nullable=True)
    website: Mapped[str | None] = mapped_column(String(300), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="prospect", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    user: Mapped[User] = relationship(back_populates="clients")
    meetings: Mapped[list[Meeting]] = relationship(
        back_populates="client",
        cascade="all, delete-orphan",
        order_by="Meeting.created_at.desc()",
    )
    analysis_jobs: Mapped[list["AnalysisJob"]] = relationship(
        back_populates="client",
        cascade="all, delete-orphan",
    )


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    source_filename: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    triage: Mapped[str] = mapped_column(Text, default="", nullable=False)
    selected_agents: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    final_report: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    client: Mapped[Client] = relationship(back_populates="meetings")
    analysis_job: Mapped["AnalysisJob | None"] = relationship(
        back_populates="meeting",
        uselist=False,
    )


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    source_filename: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    input_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    meeting_id: Mapped[int | None] = mapped_column(
        ForeignKey("meetings.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
    user: Mapped[User] = relationship(back_populates="analysis_jobs")
    client: Mapped[Client] = relationship(back_populates="analysis_jobs")
    meeting: Mapped[Meeting | None] = relationship(back_populates="analysis_job")
