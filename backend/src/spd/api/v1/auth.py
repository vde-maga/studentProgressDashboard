"""Authentication endpoints: login, token refresh and current-user profile."""

from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from spd.api.deps import (
    Principal,
    get_account_repository,
    get_current_principal,
    get_student_repository,
)
from spd.core.config import Settings
from spd.core.errors import AppError
from spd.core.security import (
    WWW_AUTHENTICATE,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from spd.domain.enums import Role
from spd.infrastructure.repositories import (
    SqlAccountRepository,
    SqlStudentRepository,
)

router = APIRouter()

logger = structlog.get_logger("spd.auth")


class LoginRequest(BaseModel):
    """Credentials submitted to obtain a token pair."""

    login: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    """A refresh token to exchange for a new token pair."""

    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    """A freshly issued pair of bearer tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfile(BaseModel):
    """The authenticated user, safe to render (never the password hash)."""

    id: int
    login: str
    email: str
    full_name: str
    role: Role
    campus_id: int
    blackholed_at: datetime | None
    created_at: datetime


def _issue_tokens(
    *, subject: int, login: str, role: Role, settings: Settings
) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(
            subject=subject, login=login, role=role, settings=settings
        ),
        refresh_token=create_refresh_token(
            subject=subject, login=login, role=role, settings=settings
        ),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Log in",
    description="Exchange a login and password for an access and refresh token.",
    responses={401: {"description": "Invalid credentials."}},
)
async def login(
    payload: LoginRequest,
    request: Request,
    accounts: Annotated[SqlAccountRepository, Depends(get_account_repository)],
) -> TokenResponse:
    account = await accounts.find_by_login(payload.login)
    if not verify_password(
        payload.password, account.password_hash if account else None
    ):
        logger.info("login_failed", login=payload.login)
        raise AppError(
            401,
            "invalid_credentials",
            "Invalid login or password.",
            headers=WWW_AUTHENTICATE,
        )
    assert account is not None
    settings: Settings = request.app.state.settings
    logger.info("login_succeeded", login=account.login, role=account.role.value)
    return _issue_tokens(
        subject=account.id,
        login=account.login,
        role=account.role,
        settings=settings,
    )


@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
    description="Exchange a valid refresh token for a new access and refresh token.",
    responses={401: {"description": "Invalid or expired refresh token."}},
)
async def refresh(
    payload: RefreshRequest,
    request: Request,
) -> TokenResponse:
    settings: Settings = request.app.state.settings
    principal = decode_token(
        payload.refresh_token, settings=settings, expected_type=TokenType.REFRESH
    )
    return _issue_tokens(
        subject=principal.subject,
        login=principal.login,
        role=principal.role,
        settings=settings,
    )


@router.get(
    "/auth/me",
    response_model=UserProfile,
    summary="Current user",
    description="Return the profile of the caller identified by the access token.",
    responses={401: {"description": "Missing or invalid access token."}},
)
async def me(
    principal: Annotated[Principal, Depends(get_current_principal)],
    students: Annotated[SqlStudentRepository, Depends(get_student_repository)],
) -> UserProfile:
    student = await students.get_by_login(principal.login)
    if student is None:
        raise AppError(
            404, "user_not_found", "The authenticated user no longer exists."
        )
    return UserProfile(
        id=student.id,
        login=student.login,
        email=student.email,
        full_name=student.full_name,
        role=student.role,
        campus_id=student.campus_id,
        blackholed_at=student.blackholed_at,
        created_at=student.created_at,
    )
