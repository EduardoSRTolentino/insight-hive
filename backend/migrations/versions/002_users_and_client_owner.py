"""Usuários e dono do cliente.

Revision ID: 002_users
Revises: 001_initial
Create Date: 2026-08-16
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_users"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CLIENT_COLUMNS = (
    "id",
    "user_id",
    "name",
    "name_key",
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
    "created_at",
)


def _clients_table(name: str, *, with_user: bool) -> None:
    columns = [
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
    ]
    if with_user:
        columns.append(sa.Column("user_id", sa.Integer(), nullable=False))
    columns.extend(
        [
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
        ]
    )
    constraints: list[sa.SchemaItem] = []
    if with_user:
        constraints.extend(
            [
                sa.ForeignKeyConstraint(
                    ["user_id"], ["users.id"], name="fk_clients_user_id_users"
                ),
                sa.UniqueConstraint(
                    "user_id", "name_key", name="uq_clients_user_id_name_key"
                ),
            ]
        )
    else:
        constraints.append(sa.UniqueConstraint("name_key"))
    op.create_table(name, *columns, *constraints)


def upgrade() -> None:
    from security import bootstrap_admin_email, hash_password
    from settings import get_settings

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=200), nullable=False),
        sa.Column("password_hash", sa.String(length=200), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("company", sa.String(length=200), nullable=True),
        sa.Column("job_title", sa.String(length=120), nullable=True),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.Column("linkedin_url", sa.String(length=300), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email"),
    )

    settings = get_settings()
    email = bootstrap_admin_email()
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "INSERT INTO users (email, password_hash, full_name, created_at) "
            "VALUES (:email, :password_hash, :full_name, :created_at)"
        ),
        {
            "email": email,
            "password_hash": hash_password(settings.app_password),
            "full_name": settings.app_username.strip() or "Admin",
            "created_at": datetime.now(timezone.utc),
        },
    )
    admin_id = bind.execute(
        sa.text("SELECT id FROM users WHERE email = :email"),
        {"email": email},
    ).scalar()

    bind.execute(sa.text("PRAGMA foreign_keys=OFF"))
    _clients_table("clients_new", with_user=True)
    column_list = ", ".join(_CLIENT_COLUMNS)
    source_list = column_list.replace("user_id", ":uid")
    bind.execute(
        sa.text(
            f"INSERT INTO clients_new ({column_list}) "
            f"SELECT {source_list} FROM clients"
        ),
        {"uid": admin_id},
    )
    op.drop_table("clients")
    op.rename_table("clients_new", "clients")
    op.create_index("ix_clients_user_id", "clients", ["user_id"])
    bind.execute(sa.text("PRAGMA foreign_keys=ON"))


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("PRAGMA foreign_keys=OFF"))
    _clients_table("clients_old", with_user=False)
    old_columns = ", ".join(col for col in _CLIENT_COLUMNS if col != "user_id")
    bind.execute(
        sa.text(
            f"INSERT INTO clients_old ({old_columns}) "
            f"SELECT {old_columns} FROM clients"
        )
    )
    op.drop_index("ix_clients_user_id", table_name="clients")
    op.drop_table("clients")
    op.rename_table("clients_old", "clients")
    bind.execute(sa.text("PRAGMA foreign_keys=ON"))
    op.drop_table("users")
