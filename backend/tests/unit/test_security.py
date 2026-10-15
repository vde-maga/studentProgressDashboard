"""Unit tests for password hashing and JWT issuing/verification."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from spd.core.config import Environment, Settings
from spd.core.errors import AppError
from spd.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from spd.domain.enums import Role


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        environment=Environment.TESTING,
        jwt_secret="test-secret-value-that-is-long-enough-1234",
    )


def test_hash_password_is_salted_and_verifies() -> None:
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")

    assert first != second, "each hash must use a fresh salt"
    assert verify_password("correct horse battery staple", first)
    assert not verify_password("wrong password", first)


def test_verify_password_rejects_missing_or_garbage_hash() -> None:
    assert not verify_password("anything", None)
    assert not verify_password("anything", "not-a-valid-hash")


def test_access_token_round_trips(settings: Settings) -> None:
    token = create_access_token(
        subject=42, login="msilva", role=Role.STUDENT, settings=settings
    )

    payload = decode_token(token, settings=settings, expected_type=TokenType.ACCESS)

    assert payload.subject == 42
    assert payload.login == "msilva"
    assert payload.role is Role.STUDENT
    assert payload.token_type is TokenType.ACCESS
    assert payload.expires_at > datetime.now(UTC)
    assert payload.token_id


def test_tokens_are_signed_with_a_unique_id(settings: Settings) -> None:
    first = decode_token(
        create_access_token(subject=1, login="a", role=Role.STUDENT, settings=settings),
        settings=settings,
        expected_type=TokenType.ACCESS,
    )
    second = decode_token(
        create_access_token(subject=1, login="a", role=Role.STUDENT, settings=settings),
        settings=settings,
        expected_type=TokenType.ACCESS,
    )

    assert first.token_id != second.token_id


def test_refresh_token_cannot_be_used_as_access(settings: Settings) -> None:
    refresh = create_refresh_token(
        subject=1, login="a", role=Role.STUDENT, settings=settings
    )

    with pytest.raises(AppError) as excinfo:
        decode_token(refresh, settings=settings, expected_type=TokenType.ACCESS)

    assert excinfo.value.status_code == 401
    assert excinfo.value.code == "invalid_token"


def test_expired_token_is_rejected(settings: Settings) -> None:
    now = datetime.now(UTC)
    expired = jwt.encode(
        {
            "sub": "1",
            "login": "a",
            "role": "student",
            "type": "access",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
            "jti": "expired",
        },
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(AppError) as excinfo:
        decode_token(expired, settings=settings, expected_type=TokenType.ACCESS)

    assert excinfo.value.code == "token_expired"


def test_token_signed_with_another_secret_is_rejected(settings: Settings) -> None:
    other = Settings(
        _env_file=None,
        environment=Environment.TESTING,
        jwt_secret="a-completely-different-secret-value-99",
    )
    token = create_access_token(subject=1, login="a", role=Role.STUDENT, settings=other)

    with pytest.raises(AppError) as excinfo:
        decode_token(token, settings=settings, expected_type=TokenType.ACCESS)

    assert excinfo.value.code == "invalid_token"


def test_tampered_token_is_rejected(settings: Settings) -> None:
    token = create_access_token(
        subject=1, login="a", role=Role.STUDENT, settings=settings
    )
    header, payload, signature = token.split(".")

    with pytest.raises(AppError):
        decode_token(
            f"{header}.{payload}.{signature[:-2]}xx",
            settings=settings,
            expected_type=TokenType.ACCESS,
        )


def test_role_claim_is_read_from_the_token(settings: Settings) -> None:
    token = jwt.decode(
        create_access_token(
            subject=7, login="staff", role=Role.STAFF, settings=settings
        ),
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )
    assert token["role"] == "staff"
