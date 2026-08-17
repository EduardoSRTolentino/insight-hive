"""SQLite via SQLAlchemy: engine, sessão e migrações Alembic."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from settings import get_settings

BACKEND_DIR = Path(__file__).resolve().parent


def _sqlite_file_path(database_url: str) -> Path | None:
    if not database_url.startswith("sqlite:///"):
        return None
    path = Path(database_url[len("sqlite:///") :])
    if not path.is_absolute():
        path = BACKEND_DIR / path
    return path


def _ensure_sqlite_dir(database_url: str) -> None:
    path = _sqlite_file_path(database_url)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)


DATABASE_URL = get_settings().database_url
_ensure_sqlite_dir(DATABASE_URL)

connect_args: dict[str, bool] = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", DATABASE_URL)
    return config


def init_db() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    config = _alembic_config()
    if "clients" in tables and "alembic_version" not in tables:
        command.stamp(config, "001_initial")
    command.upgrade(config, "head")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
