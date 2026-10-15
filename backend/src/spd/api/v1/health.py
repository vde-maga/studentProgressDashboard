"""Health probes: liveness and readiness."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from spd import __version__
from spd.core.errors import AppError
from spd.infrastructure.db.session import get_session

router = APIRouter()

logger = structlog.get_logger("spd.health")


class HealthResponse(BaseModel):
    """Liveness payload: the API process is up and serving."""

    status: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness payload: dependencies required to serve traffic are up."""

    status: str
    database: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns the API status, version and active environment.",
)
async def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        version=__version__,
        environment=settings.environment.value,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Checks the database connection; 503 when it is unreachable.",
    responses={503: {"description": "A dependency is unavailable."}},
)
async def readiness(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReadinessResponse:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("readiness_failed", error=str(exc))
        raise AppError(
            503,
            "database_unavailable",
            "Database is not reachable.",
        ) from exc
    return ReadinessResponse(status="ready", database="up")
