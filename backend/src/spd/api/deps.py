"""Shared FastAPI dependencies: authentication, authorisation, repositories."""

from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from spd.core.config import Settings
from spd.core.errors import AppError
from spd.core.security import (
    WWW_AUTHENTICATE,
    TokenPayload,
    TokenType,
    decode_token,
)
from spd.domain.enums import Role
from spd.infrastructure.db.session import get_session
from spd.infrastructure.repositories import (
    SqlAccountRepository,
    SqlStudentRepository,
)

__all__ = [
    "Principal",
    "get_account_repository",
    "get_current_principal",
    "get_student_repository",
    "require_roles",
]

Principal = TokenPayload

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_account_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SqlAccountRepository:
    """Provide the credential repository for the current request."""
    return SqlAccountRepository(session)


async def get_student_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SqlStudentRepository:
    """Provide the student repository for the current request."""
    return SqlStudentRepository(session)


async def get_current_principal(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ],
) -> Principal:
    """Resolve the authenticated principal from the ``Authorization`` header.

    Raises ``AppError(401)`` when the header is missing or the token invalid.
    """
    if credentials is None or not credentials.credentials:
        raise AppError(
            401,
            "not_authenticated",
            "Authentication credentials were not provided.",
            headers=WWW_AUTHENTICATE,
        )
    settings: Settings = request.app.state.settings
    return decode_token(
        credentials.credentials, settings=settings, expected_type=TokenType.ACCESS
    )


def require_roles(*roles: Role) -> Callable[..., Coroutine[Any, Any, Principal]]:
    """Build a dependency that only allows the given roles.

    Usage: ``Depends(require_roles(Role.ADMIN, Role.STAFF))``.
    """
    if not roles:
        raise ValueError("require_roles needs at least one role")
    allowed = frozenset(roles)

    async def _dependency(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
        if principal.role not in allowed:
            raise AppError(
                403,
                "forbidden",
                "Your role is not allowed to access this resource.",
            )
        return principal

    return _dependency
