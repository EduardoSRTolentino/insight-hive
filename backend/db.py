"""SQLite via SQLAlchemy: engine, sessão e criação das tabelas."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "insight_hive.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

connect_args: dict[str, bool] = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


CLIENT_NEW_COLUMNS: tuple[tuple[str, str], ...] = (
    ("segment", "VARCHAR(120)"),
    ("company_size", "VARCHAR(40)"),
    ("website", "VARCHAR(300)"),
    ("city", "VARCHAR(120)"),
    ("state", "VARCHAR(2)"),
    ("contact_name", "VARCHAR(200)"),
    ("contact_role", "VARCHAR(120)"),
    ("contact_email", "VARCHAR(200)"),
    ("contact_phone", "VARCHAR(40)"),
    ("owner", "VARCHAR(200)"),
    ("status", "VARCHAR(40) DEFAULT 'prospect'"),
    ("notes", "TEXT"),
)


def ensure_client_columns() -> None:
    inspector = inspect(engine)
    if "clients" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("clients")}
    with engine.begin() as connection:
        for name, ddl_type in CLIENT_NEW_COLUMNS:
            if name in existing:
                continue
            connection.execute(text(f"ALTER TABLE clients ADD COLUMN {name} {ddl_type}"))


def init_db() -> None:
    from models import Base

    Base.metadata.create_all(bind=engine)
    ensure_client_columns()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
