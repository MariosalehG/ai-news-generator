# pydantic-settings: loads AI_NEWS_DATABASE_URL, OPENAI_API_KEY, SMTP_*, DIGEST_RECIPIENT from env/.env
# (DATABASE_URL is deliberately avoided: it's already claimed by an unrelated project in this shell's env)
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[1] / ".env", extra="ignore")

    database_url: str = Field(validation_alias="AI_NEWS_DATABASE_URL")

    openai_api_key: str | None = None

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    digest_recipient: str | None = None


settings = Settings()
