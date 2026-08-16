"""Schema inicial: clients e meetings.

Revision ID: 001_initial
Revises:
Create Date: 2026-08-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("name_key", sa.String(length=200), nullable=False),
        sa.Column("segment", sa.String(length=120), nullable=True),
        sa.Column("company_size", sa.String(length=40), nullable=True),
        sa.Column("website", sa.String(length=300), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.Column("contact_name", sa.String(length=200), nullable=True),
        sa.Column("contact_role", sa.String(length=120), nullable=True),
        sa.Column("contact_email", sa.String(length=200), nullable=True),
        sa.Column("contact_phone", sa.String(length=40), nullable=True),
        sa.Column("owner", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="prospect"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name_key"),
    )
    op.create_table(
        "meetings",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("source_filename", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("triage", sa.Text(), nullable=False, server_default=""),
        sa.Column("selected_agents", sa.JSON(), nullable=False),
        sa.Column("final_report", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
    )
    op.create_index("ix_meetings_client_id", "meetings", ["client_id"])


def downgrade() -> None:
    op.drop_index("ix_meetings_client_id", table_name="meetings")
    op.drop_table("meetings")
    op.drop_table("clients")
