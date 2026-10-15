"""Health (liveness) endpoint."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from spd import __version__

router = APIRouter()


class HealthResponse(BaseModel):
    """Liveness payload: the API process is up and serving."""

    status: str
    version: str
    environment: str


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
