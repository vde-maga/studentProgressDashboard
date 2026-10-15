"""Cohort leaderboard endpoint, visible to any authenticated user."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from spd.api.deps import Principal, get_analytics_service, get_current_principal
from spd.application.analytics import AnalyticsService

router = APIRouter()


class LeaderboardEntryOut(BaseModel):
    """One ranked row of the cohort leaderboard."""

    rank: int
    login: str
    full_name: str
    campus_code: str
    xp_total: int
    level: Decimal
    projects_done: int


@router.get(
    "/leaderboard",
    response_model=list[LeaderboardEntryOut],
    summary="Cohort leaderboard",
    description="Return a page of the cohort ranked by total XP.",
    responses={401: {"description": "Missing or invalid access token."}},
)
async def get_leaderboard(
    _: Annotated[Principal, Depends(get_current_principal)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[LeaderboardEntryOut]:
    rows = await service.leaderboard(limit=limit, offset=offset)
    return [
        LeaderboardEntryOut(
            rank=row.rank,
            login=row.student.login,
            full_name=row.student.full_name,
            campus_code=row.campus.code,
            xp_total=row.xp_total,
            level=row.level,
            projects_done=row.projects_done,
        )
        for row in rows
    ]
