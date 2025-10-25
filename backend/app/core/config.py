from __future__ import annotations

from functools import lru_cache
from typing import Any

from pathlib import Path
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[3] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "SmartHire Gateway"
    debug: bool = False
    docs_url: str | None = "/docs"
    redoc_url: str | None = "/redoc"
    openapi_url: str | None = "/openapi.json"
    log_level: str = "INFO"

    backend_cors_origins: list[str] | str | None = Field(default=None)

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires: int = 60 * 60  # seconds

    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"

    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_whatsapp_from: str | None = None
    twilio_validation_token: str | None = None

    openai_api_key: str | None = None

    google_service_account_json: str | None = None
    google_sheets_id: str | None = None
    google_drive_folder_id: str | None = None

    storage_mode: str = Field(
        default="google",
        description="google|local. If local, write extracts to data/dev/ for demo without credentials.",
    )

    allowed_origins: list[str] = Field(default_factory=list)

    @validator("backend_cors_origins", pre=True)
    def assemble_cors_origins(cls, value: Any) -> list[str]:
        origins: set[str] = set()
        if isinstance(value, list):
            source = [str(item) for item in value]
        elif isinstance(value, str) and value:
            source = [origin for origin in value.split(",")]
        else:
            source = []

        for origin in source:
            normalized = cls._normalize_origin(origin)
            if not normalized:
                continue
            origins.add(normalized)
            origins.add(f"{normalized}/")
        return sorted(origins)
        return []

    @validator("allowed_origins", pre=True, always=True)
    def sync_allowed_origins(cls, value: list[str], values: dict[str, Any]) -> list[str]:
        cors = values.get("backend_cors_origins") or []
        if value:
            return [cls._normalize_origin(str(item)) for item in value if str(item).strip()]
        return cors

    @validator("debug", pre=True)
    def coerce_debug(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes", "on"}:
                return True
            if lowered in {"false", "0", "no", "off"}:
                return False
        return False

    @staticmethod
    def _normalize_origin(origin: str) -> str:
        cleaned = origin.strip()
        if not cleaned:
            return ""
        return cleaned.rstrip("/")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
