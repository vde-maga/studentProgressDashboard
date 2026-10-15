"""Student-facing analytics endpoints.

Detailed analytics are owner-only: a student may read their own data and staff
or admins may read anyone's (enforced via ``ensure_can_view``). The roster
listing itself is staff/admin only, since it exposes every student's account.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from spd.api.deps import (
    Principal,
    ensure_can_view,
    get_analytics_service,
    get_current_principal,
    get_student_repository,
    require_roles,
)
from spd.application.analytics import AnalyticsService
from spd.domain.enums import ActivityKind, Role
from spd.infrastructure.repositories import SqlStudentRepository

router = APIRouter()


class StudentOut(BaseModel):
    """A student account as returned by the roster."""

    id: int
    login: str
    full_name: str
    role: Role
    campus_id: int
    blackholed_at: datetime | None
    created_at: datetime


class StudentListResponse(BaseModel):
    """A page of students with the total available."""

    items: list[StudentOut]
    total: int
    limit: int
    offset: int


class CampusOut(BaseModel):
    """The campus a student belongs to."""

    id: int
    code: str
    name: str
    city: str
    country: str


class StudentProfileOut(BaseModel):
    """A student's profile enriched with rank and level progression."""

    id: int
    login: str
    full_name: str
    role: Role
    campus: CampusOut
    xp_total: int
    level: Decimal
    level_progress: Decimal
    projects_done: int
    rank: int
    current_streak: int
    blackholed_at: datetime | None
    created_at: datetime


class ProgressPointOut(BaseModel):
    """One day of a student's progress time series."""

    day: date
    xp_total: int
    level: Decimal
    projects_done: int


class ActivityItemOut(BaseModel):
    """An activity event in a student's timeline."""

    id: int
    kind: ActivityKind
    day: date
    xp_delta: int
    project_slug: str | None
    occurred_at: datetime


class SkillLevelOut(BaseModel):
    """A named skill and the student's current level in it."""

    code: str
    name: str
    level: Decimal


@router.get(
    "/students",
    response_model=StudentListResponse,
    summary="List students",
    description="Return a page of student accounts (staff and admins only).",
    responses={403: {"description": "The caller is not staff or admin."}},
)
async def list_students(
    _: Annotated[Principal, Depends(require_roles(Role.STAFF, Role.ADMIN))],
    students: Annotated[SqlStudentRepository, Depends(get_student_repository)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> StudentListResponse:
    page = await students.list_students(limit=limit, offset=offset)
    return StudentListResponse(
        items=[
            StudentOut(
                id=student.id,
                login=student.login,
                full_name=student.full_name,
                role=student.role,
                campus_id=student.campus_id,
                blackholed_at=student.blackholed_at,
                created_at=student.created_at,
            )
            for student in page
        ],
        total=await students.count(),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/students/{login}",
    response_model=StudentProfileOut,
    summary="Student profile",
    description="Return a student's profile, rank and level progression.",
    responses={
        403: {"description": "The caller may not view this student."},
        404: {"description": "No such student."},
    },
)
async def get_student_profile(
    login: str,
    principal: Annotated[Principal, Depends(get_current_principal)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> StudentProfileOut:
    ensure_can_view(principal, login)
    profile = await service.student_profile(login)
    return StudentProfileOut(
        id=profile.student.id,
        login=profile.student.login,
        full_name=profile.student.full_name,
        role=profile.student.role,
        campus=CampusOut(
            id=profile.campus.id,
            code=profile.campus.code,
            name=profile.campus.name,
            city=profile.campus.city,
            country=profile.campus.country,
        ),
        xp_total=profile.xp_total,
        level=profile.level,
        level_progress=profile.level_progress,
        projects_done=profile.projects_done,
        rank=profile.rank,
        current_streak=profile.current_streak,
        blackholed_at=profile.student.blackholed_at,
        created_at=profile.student.created_at,
    )


@router.get(
    "/students/{login}/progress",
    response_model=list[ProgressPointOut],
    summary="Student progress time series",
    description="Return a student's daily progress points, oldest first.",
    responses={
        403: {"description": "The caller may not view this student."},
        404: {"description": "No such student."},
    },
)
async def get_student_progress(
    login: str,
    principal: Annotated[Principal, Depends(get_current_principal)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    since: Annotated[date | None, Query()] = None,
    until: Annotated[date | None, Query()] = None,
) -> list[ProgressPointOut]:
    ensure_can_view(principal, login)
    points = await service.student_progress(login, since=since, until=until)
    return [
        ProgressPointOut(
            day=point.day,
            xp_total=point.xp_total,
            level=point.level,
            projects_done=point.projects_done,
        )
        for point in points
    ]


@router.get(
    "/students/{login}/activity",
    response_model=list[ActivityItemOut],
    summary="Student activity feed",
    description="Return a student's most recent activity, newest first.",
    responses={
        403: {"description": "The caller may not view this student."},
        404: {"description": "No such student."},
    },
)
async def get_student_activity(
    login: str,
    principal: Annotated[Principal, Depends(get_current_principal)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ActivityItemOut]:
    ensure_can_view(principal, login)
    items = await service.student_activity(login, limit=limit)
    return [
        ActivityItemOut(
            id=item.id,
            kind=item.kind,
            day=item.day,
            xp_delta=item.xp_delta,
            project_slug=item.project_slug,
            occurred_at=item.occurred_at,
        )
        for item in items
    ]


@router.get(
    "/students/{login}/skills",
    response_model=list[SkillLevelOut],
    summary="Student skills",
    description="Return a student's skills with their current levels.",
    responses={
        403: {"description": "The caller may not view this student."},
        404: {"description": "No such student."},
    },
)
async def get_student_skills(
    login: str,
    principal: Annotated[Principal, Depends(get_current_principal)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> list[SkillLevelOut]:
    ensure_can_view(principal, login)
    skills = await service.student_skills(login)
    return [
        SkillLevelOut(code=skill.code, name=skill.name, level=skill.level)
        for skill in skills
    ]
