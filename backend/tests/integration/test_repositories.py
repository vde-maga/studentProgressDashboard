"""Repository integration tests: real SQL against a real database."""

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spd.infrastructure.db import models as orm
from spd.infrastructure.repositories import (
    SqlAnalyticsRepository,
    SqlStudentRepository,
)
from spd.infrastructure.seed import SeedConfig, Seeder

pytestmark = pytest.mark.integration

_SEED = SeedConfig(
    seed=7, student_count=8, days=45, end_date=date(2026, 10, 15), reset=True
)


async def _seed(session: AsyncSession) -> None:
    await Seeder(_SEED).run(session)


async def test_student_repository_reads_seeded_cohort(
    session: AsyncSession,
) -> None:
    await _seed(session)
    repository = SqlStudentRepository(session)

    assert await repository.count() == _SEED.student_count

    page = await repository.list_students(limit=3, offset=0)
    assert [student.login for student in page] == sorted(
        student.login for student in page
    )

    first = page[0]
    fetched = await repository.get_by_login(first.login)
    assert fetched == first


async def test_student_repository_returns_none_for_unknown_login(
    session: AsyncSession,
) -> None:
    assert await SqlStudentRepository(session).get_by_login("nobody") is None


async def test_analytics_repository_returns_ordered_snapshots(
    session: AsyncSession,
) -> None:
    await _seed(session)
    student_id = await session.scalar(select(orm.User.id).order_by(orm.User.id))
    assert student_id is not None
    repository = SqlAnalyticsRepository(session)

    snapshots = await repository.daily_snapshots(student_id)
    assert snapshots, "seeded student should have snapshots"
    assert [s.day for s in snapshots] == sorted(s.day for s in snapshots)
    assert snapshots[-1].xp_total == await repository.total_xp(student_id)


async def test_analytics_repository_since_filter(session: AsyncSession) -> None:
    await _seed(session)
    student_id = await session.scalar(select(orm.User.id).order_by(orm.User.id))
    assert student_id is not None
    repository = SqlAnalyticsRepository(session)

    snapshots = await repository.daily_snapshots(student_id)
    cutoff = snapshots[len(snapshots) // 2].day
    filtered = await repository.daily_snapshots(student_id, since=cutoff)

    assert filtered
    assert all(snapshot.day >= cutoff for snapshot in filtered)
    assert len(filtered) <= len(snapshots)
