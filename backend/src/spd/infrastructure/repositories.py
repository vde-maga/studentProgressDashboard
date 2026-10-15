"""SQLAlchemy implementations of the domain repository ports."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from spd.domain.entities import Account, DailySnapshot, Student
from spd.infrastructure import mappers
from spd.infrastructure.db import models as orm

__all__ = [
    "SqlAccountRepository",
    "SqlAnalyticsRepository",
    "SqlStudentRepository",
]


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


class SqlAnalyticsRepository:
    """Read access to precomputed progress time series."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def daily_snapshots(
        self, student_id: int, *, since: date | None = None
    ) -> list[DailySnapshot]:
        stmt = (
            select(orm.DailySnapshot)
            .where(orm.DailySnapshot.user_id == student_id)
            .order_by(orm.DailySnapshot.day)
        )
        if since is not None:
            stmt = stmt.where(orm.DailySnapshot.day >= since)
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
