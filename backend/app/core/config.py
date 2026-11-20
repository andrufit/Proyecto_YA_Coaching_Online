from pathlib import Path

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Y&A Coaching Online API"

    database_url: str
    frontend_url: str = "http://localhost:5173"
    cors_extra_origins: str = ""

    @property
    def browser_origins(self) -> list[str]:
        """Explicit browser origins, including the frontend used in email links."""
        origins = []
        for raw in [self.frontend_url, *self.cors_extra_origins.split(",")]:
            value = raw.strip()
            if not value:
                continue
            url = AnyHttpUrl(value)
            if (
                not url.host or "*" in url.host or url.username or url.password
                or url.query is not None or url.fragment is not None
                or url.path not in (None, "/")
            ):
                raise ValueError("Configura el origen del frontend con esquema, dominio y puerto opcional.")
            origin = str(url).rstrip("/")
            if origin not in origins:
                origins.append(origin)
        return origins

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
    )

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_security: str = "starttls"
    password_reset_minutes: int = Field(default=20, ge=5, le=60)

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
