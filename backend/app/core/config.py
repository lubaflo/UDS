from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "UDS CRM Backend"
    APP_VERSION: str = "1.0.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    DATABASE_URL: str = "sqlite:///../data/app.db"
    SQLITE_WAL: bool = True
    SQLITE_SYNCHRONOUS_NORMAL: bool = True

    TELEGRAM_BOT_TOKEN: str = ""
    JWT_SECRET: str = "change-me-please"
    JWT_ALG: str = "HS256"
    JWT_TTL_SECONDS: int = 60 * 60 * 24

    DEFAULT_SALON_NAME: str = "My CRM"
    ADMIN_TG_IDS: str = ""

    CORS_ALLOW_ORIGINS: str = "*"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_db_url(cls, value: str) -> str:
        if value.startswith("sqlite:///"):
            raw = value.removeprefix("sqlite:///")
            db_path = Path(raw)
            if "data" not in db_path.parts:
                raise ValueError("SQLite database file must be inside ./data directory")
        return value


settings = Settings()
