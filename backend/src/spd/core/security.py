"""Password hashing and stateless JWT issuing/verification.

Kept free of FastAPI and database concerns so it is trivially unit-testable.
Access and refresh tokens are plain signed JWTs (see ADR 0002): no server-side
state, so tokens are not individually revocable in this phase. Never log or
return any value produced here except the tokens handed to the client.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from spd.core.config import Settings
from spd.core.errors import AppError
from spd.domain.enums import Role

__all__ = [
    "WWW_AUTHENTICATE",
    "TokenPayload",
    "TokenType",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "hash_password",
    "verify_password",
]

_hasher = PasswordHasher()

# Standard challenge sent with 401 responses so clients know how to authenticate.
WWW_AUTHENTICATE: dict[str, str] = {"WWW-Authenticate": "Bearer"}

# A syntactically valid hash used to equalise timing when the login is unknown,
# preventing user enumeration via response timing. It never matches a password.
_DUMMY_HASH = _hasher.hash("timing-equalisation-dummy")


class TokenType(StrEnum):
    """Discriminator carried in the ``type`` claim."""

    ACCESS = "access"
    REFRESH = "refresh"


@dataclass(frozen=True, slots=True)
class TokenPayload:
    """Verified claims extracted from a token."""

    subject: int
    login: str
    role: Role
    token_type: TokenType
    issued_at: datetime
    expires_at: datetime
    token_id: str


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Return whether ``password`` matches ``password_hash``.

    A missing hash still performs a verification against a dummy so that the
    cost — and therefore the response time — does not reveal unknown accounts.
    """
    candidate = password_hash or _DUMMY_HASH
    try:
        _hasher.verify(candidate, password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    return password_hash is not None


def _encode(claims: dict[str, object], settings: Settings) -> str:
    return jwt.encode(
        claims,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def _new_token(
    *,
    subject: int,
    login: str,
    role: Role,
    token_type: TokenType,
    ttl: timedelta,
    settings: Settings,
) -> str:
    issued_at = datetime.now(UTC)
    claims: dict[str, object] = {
        "sub": str(subject),
        "login": login,
        "role": role.value,
        "type": token_type.value,
        "iat": issued_at,
        "exp": issued_at + ttl,
        "jti": uuid.uuid4().hex,
    }
    return _encode(claims, settings)


def create_access_token(
    *, subject: int, login: str, role: Role, settings: Settings
) -> str:
    """Issue a short-lived access token."""
    return _new_token(
        subject=subject,
        login=login,
        role=role,
        token_type=TokenType.ACCESS,
        ttl=timedelta(minutes=settings.jwt_access_token_expire_minutes),
        settings=settings,
    )


def create_refresh_token(
    *, subject: int, login: str, role: Role, settings: Settings
) -> str:
    """Issue a long-lived refresh token."""
    return _new_token(
        subject=subject,
        login=login,
        role=role,
        token_type=TokenType.REFRESH,
        ttl=timedelta(days=settings.jwt_refresh_token_expire_days),
        settings=settings,
    )


def decode_token(
    token: str, *, settings: Settings, expected_type: TokenType
) -> TokenPayload:
    """Verify a token's signature/expiry and its expected type.

    Raises ``AppError(401)`` for any invalid, expired or mistyped token.
    """
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AppError(
            401, "token_expired", "The token has expired.", headers=WWW_AUTHENTICATE
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise AppError(
            401, "invalid_token", "The token is invalid.", headers=WWW_AUTHENTICATE
        ) from exc

    if claims.get("type") != expected_type.value:
        raise AppError(
            401, "invalid_token", "The token is invalid.", headers=WWW_AUTHENTICATE
        )

    return TokenPayload(
        subject=int(claims["sub"]),
        login=str(claims["login"]),
        role=Role(claims["role"]),
        token_type=expected_type,
        issued_at=datetime.fromtimestamp(claims["iat"], tz=UTC),
        expires_at=datetime.fromtimestamp(claims["exp"], tz=UTC),
        token_id=str(claims["jti"]),
    )
