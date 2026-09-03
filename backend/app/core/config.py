from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Y&A Coaching Online API"

    database_url: str
    frontend_url: str = "http://localhost:5173"

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
    )

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()