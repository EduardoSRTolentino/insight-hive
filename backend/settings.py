"""Configuração tipada da aplicação, lida uma vez a partir do ambiente / `.env`."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "insight_hive.db"

_OLLAMA_DEFAULTS = {
    "ollama_model": "gpt-oss:20b",
    "ollama_base_url": "http://127.0.0.1:11434",
    "ollama_reasoning": "low",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_username: str = "admin"
    app_password: str = "admin"
    jwt_secret_key: str = "change-this-secret-key"
    jwt_expire_minutes: int = 60

    ollama_model: str = "gpt-oss:20b"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_reasoning: str = "low"
    max_specialists: int = 2
    num_predict: int = 512
    num_predict_synthesis: int = 2048

    transcript_clean: str = "1"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    database_url: str = Field(default=f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")
    max_upload_bytes: int = 5_242_880
    allow_registration: str = ""
    auth_rate_limit: int = 20
    auth_rate_window_seconds: int = 60

    @field_validator("ollama_model", "ollama_base_url", "ollama_reasoning", mode="before")
    @classmethod
    def nonempty_ollama(cls, value: object, info: ValidationInfo) -> object:
        if value is None or (isinstance(value, str) and not value.strip()):
            return _OLLAMA_DEFAULTS[info.field_name]
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("max_specialists")
    @classmethod
    def clamp_max_specialists(cls, value: int) -> int:
        return max(1, min(12, value))

    @field_validator("num_predict")
    @classmethod
    def clamp_num_predict(cls, value: int) -> int:
        return max(128, min(8192, value))

    @field_validator("num_predict_synthesis")
    @classmethod
    def clamp_num_predict_synthesis(cls, value: int) -> int:
        return max(256, min(8192, value))

    @field_validator("auth_rate_limit")
    @classmethod
    def clamp_auth_rate_limit(cls, value: int) -> int:
        return max(0, value)

    @field_validator("auth_rate_window_seconds")
    @classmethod
    def clamp_auth_rate_window(cls, value: int) -> int:
        return max(1, min(3600, value))

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def transcript_clean_enabled(self) -> bool:
        return str(self.transcript_clean).strip().lower() not in {"0", "false", "off", "no"}

    @property
    def registration_enabled(self) -> bool:
        raw = str(self.allow_registration).strip().lower()
        if raw in {"0", "false", "off", "no"}:
            return False
        if raw in {"1", "true", "on", "yes"}:
            return True
        return self.app_env.lower() not in {"production", "prod"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
