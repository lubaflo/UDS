from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Важно: backend запускается из папки backend, а data лежит уровнем выше
    DATABASE_URL: str = "sqlite:///../data/app.db"

    SQLITE_WAL: bool = True
    SQLITE_SYNCHRONOUS_NORMAL: bool = True

    # Если ты используешь Telegram verify init_data
    TELEGRAM_BOT_TOKEN: str = ""


settings = Settings()