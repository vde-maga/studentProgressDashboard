"""Tests for environment-aware application settings."""

import pytest
from pydantic import ValidationError

from spd.core.config import Environment, Settings


def test_defaults_target_development() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment is Environment.DEVELOPMENT
    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.docs_enabled is True
    assert settings.jwt_access_token_expire_minutes == 15


def test_production_requires_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(_env_file=None, environment=Environment.PRODUCTION)


def test_production_rejects_weak_or_default_secret() -> None:
    default_secret = Settings(_env_file=None).jwt_secret.get_secret_value()

    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(
            _env_file=None,
            environment=Environment.PRODUCTION,
            jwt_secret=default_secret,
        )

    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(_env_file=None, environment=Environment.PRODUCTION, jwt_secret="short")


def test_production_accepts_strong_secret() -> None:
    settings = Settings(
        _env_file=None,
        environment=Environment.PRODUCTION,
        jwt_secret="a" * 48,
    )

    assert settings.environment is Environment.PRODUCTION


def test_cors_origins_accepts_csv_string() -> None:
    settings = Settings(
        _env_file=None,
        cors_origins="http://a.test, http://b.test",
    )

    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_cors_origins_accepts_json_list() -> None:
    settings = Settings(_env_file=None, cors_origins='["http://a.test"]')

    assert settings.cors_origins == ["http://a.test"]


def test_invalid_environment_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="staging")
