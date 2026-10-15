"""Environment-aware application settings."""

import json
from enum import StrEnum
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_MIN_STRONG_SECRET = 32

# Publicly-known placeholder used only for local development and tests. It is
# long enough for HS256 (>= 32 bytes) but must never reach production, which is
# enforced by the validator below.
_DEV_JWT_SECRET = "dev-only-insecure-secret-change-me"


class Environment(StrEnum):
    """Runtime environment the API is configured for."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Environment = Environment.DEVELOPMENT
    database_url: str = "postgresql+psycopg://spd:spd@localhost:5432/spd_dev"
    jwt_secret: SecretStr = SecretStr(_DEV_JWT_SECRET)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=15, ge=1)
    jwt_refresh_token_expire_days: int = Field(default=14, ge=1)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    docs_enabled: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            return [origin.strip() for origin in text.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _require_strong_secret_in_production(self) -> "Settings":
        if self.environment is Environment.PRODUCTION:
            secret = self.jwt_secret.get_secret_value()
            if secret == _DEV_JWT_SECRET or len(secret) < _MIN_STRONG_SECRET:
                msg = "JWT_SECRET must be a strong value (>= 32 chars) in production"
                raise ValueError(msg)
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings instance (cached)."""
    return Settings()
