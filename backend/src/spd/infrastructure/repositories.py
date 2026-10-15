"""SQLAlchemy implementations of the domain repository ports."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Subquery

from spd.domain.entities import (
    Account,
    Campus,
    DailySnapshot,
    Skill,
    SkillLevel,
    Student,
)
from spd.domain.enums import Role
from spd.domain.readmodels import (
    ActivityItem,
    CohortSummary,
    StudentProgress,
)
from spd.infrastructure import mappers
from spd.infrastructure.db import models as orm

__all__ = [
    "SqlAccountRepository",
    "SqlAnalyticsRepository",
    "SqlCampusRepository",
    "SqlCohortRepository",
    "SqlLeaderboardRepository",
    "SqlStudentRepository",
]

_ACTIVE_WINDOW_DAYS = 7
_CENTS = Decimal("0.01")


class SqlAccountRepository:
    """Read access to authentication credentials backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_login(self, login: str) -> Account | None:
        stmt = select(orm.User).where(orm.User.login == login)
        row = await self._session.scalar(stmt)
        return mappers.to_account(row) if row is not None else None


class SqlStudentRepository:
    """Read access to student accounts backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_login(self, login: str) -> Student | None:
        stmt = select(orm.User).where(orm.User.login == login)
        row = await self._session.scalar(stmt)
        return mappers.to_student(row) if row is not None else None

    async def list_students(self, *, limit: int, offset: int) -> list[Student]:
        stmt = select(orm.User).order_by(orm.User.login).limit(limit).offset(offset)
        rows = (await self._session.scalars(stmt)).all()
        return [mappers.to_student(row) for row in rows]

    async def count(self) -> int:
        stmt = select(func.count()).select_from(orm.User)
        return await self._session.scalar(stmt) or 0


class SqlCampusRepository:
    """Read access to campuses backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, campus_id: int) -> Campus | None:
        row = await self._session.get(orm.Campus, campus_id)
        return mappers.to_campus(row) if row is not None else None


class SqlAnalyticsRepository:
    """Read access to precomputed progress time series."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def daily_snapshots(
        self,
        student_id: int,
        *,
        since: date | None = None,
        until: date | None = None,
    ) -> list[DailySnapshot]:
        stmt = (
            select(orm.DailySnapshot)
            .where(orm.DailySnapshot.user_id == student_id)
            .order_by(orm.DailySnapshot.day)
        )
        if since is not None:
            stmt = stmt.where(orm.DailySnapshot.day >= since)
        if until is not None:
            stmt = stmt.where(orm.DailySnapshot.day <= until)
        rows = (await self._session.scalars(stmt)).all()
        return [mappers.to_daily_snapshot(row) for row in rows]

    async def total_xp(self, student_id: int) -> int:
        stmt = (
            select(orm.DailySnapshot.xp_total)
            .where(orm.DailySnapshot.user_id == student_id)
            .order_by(orm.DailySnapshot.day.desc())
            .limit(1)
        )
        return await self._session.scalar(stmt) or 0

    async def recent_activity(
        self, student_id: int, *, limit: int
    ) -> list[ActivityItem]:
        stmt = (
            select(orm.ActivityEvent, orm.User.login, orm.Project.slug)
            .join(orm.User, orm.User.id == orm.ActivityEvent.user_id)
            .outerjoin(orm.Project, orm.Project.id == orm.ActivityEvent.project_id)
            .where(orm.ActivityEvent.user_id == student_id)
            .order_by(orm.ActivityEvent.id.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            mappers.to_activity_item(event, login=login, project_slug=slug)
            for event, login, slug in rows
        ]

    async def events_after(self, last_id: int, *, limit: int) -> list[ActivityItem]:
        stmt = (
            select(orm.ActivityEvent, orm.User.login, orm.Project.slug)
            .join(orm.User, orm.User.id == orm.ActivityEvent.user_id)
            .outerjoin(orm.Project, orm.Project.id == orm.ActivityEvent.project_id)
            .where(orm.ActivityEvent.id > last_id)
            .order_by(orm.ActivityEvent.id)
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            mappers.to_activity_item(event, login=login, project_slug=slug)
            for event, login, slug in rows
        ]

    async def latest_event_id(self) -> int:
        stmt = select(func.max(orm.ActivityEvent.id))
        return await self._session.scalar(stmt) or 0

    async def skill_levels(self, student_id: int) -> list[tuple[Skill, SkillLevel]]:
        stmt = (
            select(orm.Skill, orm.SkillLevel)
            .join(orm.SkillLevel, orm.SkillLevel.skill_id == orm.Skill.id)
            .where(orm.SkillLevel.user_id == student_id)
            .order_by(orm.Skill.code)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            (mappers.to_skill(skill), mappers.to_skill_level(level))
            for skill, level in rows
        ]


def _latest_snapshot_subquery() -> Subquery[Any]:
    """Return a ``DISTINCT ON`` subquery holding each user's latest snapshot."""
    return (
        select(
            orm.DailySnapshot.user_id.label("user_id"),
            orm.DailySnapshot.xp_total.label("xp_total"),
            orm.DailySnapshot.level.label("level"),
            orm.DailySnapshot.projects_done.label("projects_done"),
        )
        .ext(distinct_on(orm.DailySnapshot.user_id))
        .order_by(orm.DailySnapshot.user_id, orm.DailySnapshot.day.desc())
        .subquery()
    )


class SqlLeaderboardRepository:
    """Read access to the cohort ranking backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ranked(self) -> list[StudentProgress]:
        latest = _latest_snapshot_subquery()
        xp_total = func.coalesce(latest.c.xp_total, 0)
        level = func.coalesce(latest.c.level, 0)
        projects_done = func.coalesce(latest.c.projects_done, 0)
        stmt = (
            select(orm.User, orm.Campus, xp_total, level, projects_done)
            .join(orm.Campus, orm.Campus.id == orm.User.campus_id)
            .outerjoin(latest, latest.c.user_id == orm.User.id)
            .where(orm.User.role == Role.STUDENT.value)
            .order_by(xp_total.desc(), orm.User.login)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            mappers.to_student_progress(
                cast("orm.User", user),
                campus=cast("orm.Campus", campus),
                xp_total=int(cast(int, xp)),
                level=Decimal(str(level_value)),
                projects_done=int(cast(int, projects)),
            )
            for user, campus, xp, level_value, projects in rows
        ]


class SqlCohortRepository:
    """Read access to cohort-wide aggregates backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def summary(self) -> CohortSummary:
        student_count = (
            await self._session.scalar(
                select(func.count())
                .select_from(orm.User)
                .where(orm.User.role == Role.STUDENT.value)
            )
            or 0
        )
        latest = _latest_snapshot_subquery()
        totals = (
            await self._session.execute(
                select(
                    func.coalesce(func.sum(latest.c.xp_total), 0),
                    func.coalesce(func.avg(latest.c.level), 0),
                    func.coalesce(func.sum(latest.c.projects_done), 0),
                )
            )
        ).one()
        total_xp, average_level, projects_done = totals
        return CohortSummary(
            student_count=int(student_count),
            total_xp=int(total_xp),
            average_level=Decimal(average_level).quantize(_CENTS),
            projects_done=int(projects_done),
            active_last_7_days=await self._active_students(),
        )

    async def _active_students(self) -> int:
        reference = await self._session.scalar(select(func.max(orm.ActivityEvent.day)))
        if reference is None:
            return 0
        cutoff = reference - timedelta(days=_ACTIVE_WINDOW_DAYS - 1)
        count = await self._session.scalar(
            select(func.count(func.distinct(orm.ActivityEvent.user_id))).where(
                orm.ActivityEvent.day >= cutoff
            )
        )
        return count or 0
