"""Cohort summary endpoint, visible to any authenticated user."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from spd.api.deps import Principal, get_analytics_service, get_current_principal
from spd.application.analytics import AnalyticsService

router = APIRouter()


class CohortSummaryOut(BaseModel):
    """Aggregate figures across the whole cohort."""

    student_count: int
    total_xp: int
    average_level: Decimal
    projects_done: int
    active_last_7_days: int


@router.get(
    "/cohort/summary",
    response_model=CohortSummaryOut,
    summary="Cohort summary",
    description="Return aggregate progress figures for the whole cohort.",
    responses={401: {"description": "Missing or invalid access token."}},
)
async def get_cohort_summary(
    _: Annotated[Principal, Depends(get_current_principal)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> CohortSummaryOut:
    summary = await service.cohort_summary()
    return CohortSummaryOut(
        student_count=summary.student_count,
        total_xp=summary.total_xp,
        average_level=summary.average_level,
        projects_done=summary.projects_done,
        active_last_7_days=summary.active_last_7_days,
    )
