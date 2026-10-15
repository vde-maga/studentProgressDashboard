"""Shared FastAPI dependencies: authentication, authorisation, repositories."""

from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from spd.application.analytics import AnalyticsService
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
    SqlAnalyticsRepository,
    SqlCampusRepository,
    SqlCohortRepository,
    SqlLeaderboardRepository,
    SqlStudentRepository,
)

__all__ = [
    "Principal",
    "ensure_can_view",
    "get_account_repository",
    "get_analytics_service",
    "get_current_principal",
    "get_stream_principal",
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


def _unauthorized() -> AppError:
    return AppError(
        401,
        "not_authenticated",
        "Authentication credentials were not provided.",
        headers=WWW_AUTHENTICATE,
    )


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
        raise _unauthorized()
    settings: Settings = request.app.state.settings
    return decode_token(
        credentials.credentials, settings=settings, expected_type=TokenType.ACCESS
    )


async def get_stream_principal(
    request: Request,
    token: Annotated[str, Query(min_length=1)],
) -> Principal:
    """Resolve the principal for SSE from a ``token`` query parameter.

    ``EventSource`` cannot set an ``Authorization`` header, so the access token
    travels as a query parameter instead (see ADR 0003).
    """
    settings: Settings = request.app.state.settings
    return decode_token(token, settings=settings, expected_type=TokenType.ACCESS)


async def get_analytics_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AnalyticsService:
    """Provide the analytics service wired to the request's session."""
    return AnalyticsService(
        students=SqlStudentRepository(session),
        campuses=SqlCampusRepository(session),
        analytics=SqlAnalyticsRepository(session),
        leaderboard=SqlLeaderboardRepository(session),
        cohort=SqlCohortRepository(session),
    )


def ensure_can_view(principal: Principal, login: str) -> None:
    """Allow staff/admin to view anyone, students to view only themselves."""
    if principal.role in {Role.STAFF, Role.ADMIN} or principal.login == login:
        return
    raise AppError(
        403,
        "forbidden",
        "You are not allowed to view another student's analytics.",
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
