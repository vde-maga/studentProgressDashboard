"""Integration tests for the analytics repositories against real SQL."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spd.domain.progress import assign_ranks
from spd.infrastructure.db import models as orm
from spd.infrastructure.repositories import (
    SqlAnalyticsRepository,
    SqlCampusRepository,
    SqlCohortRepository,
    SqlLeaderboardRepository,
)
from spd.infrastructure.seed import SeedConfig, Seeder

pytestmark = pytest.mark.integration

_SEED = SeedConfig(
    seed=11, student_count=10, days=60, end_date=date(2026, 10, 15), reset=True
)
_MAX_LEVEL = Decimal("21.00")


async def _seed(session: AsyncSession) -> None:
    await Seeder(_SEED).run(session)


async def _first_student_id(session: AsyncSession) -> int:
    student_id = await session.scalar(select(orm.User.id).order_by(orm.User.id))
    assert student_id is not None
    return student_id


async def test_leaderboard_orders_by_xp_and_ranks(session: AsyncSession) -> None:
    await _seed(session)

    ranked = await SqlLeaderboardRepository(session).ranked()

    assert len(ranked) == _SEED.student_count
    xps = [row.xp_total for row in ranked]
    assert xps == sorted(xps, reverse=True)
    assert assign_ranks(xps)[0] == 1
    for row in ranked:
        assert row.campus.code
        assert Decimal(0) <= row.level <= _MAX_LEVEL


async def test_cohort_summary_matches_the_leaderboard(session: AsyncSession) -> None:
    await _seed(session)

    ranked = await SqlLeaderboardRepository(session).ranked()
    summary = await SqlCohortRepository(session).summary()

    assert summary.student_count == len(ranked)
    assert summary.total_xp == sum(row.xp_total for row in ranked)
    assert summary.projects_done == sum(row.projects_done for row in ranked)
    assert 0 < summary.active_last_7_days <= summary.student_count
    assert Decimal(0) <= summary.average_level <= _MAX_LEVEL


async def test_activity_cursor_walks_forward(session: AsyncSession) -> None:
    await _seed(session)
    repository = SqlAnalyticsRepository(session)

    head = await repository.latest_event_id()
    assert head > 0
    assert await repository.events_after(head, limit=5) == []

    first_page = await repository.events_after(0, limit=5)
    assert [item.id for item in first_page] == sorted(item.id for item in first_page)
    assert first_page[0].student_login

    next_page = await repository.events_after(first_page[-1].id, limit=5)
    assert all(item.id > first_page[-1].id for item in next_page)


async def test_recent_activity_is_newest_first(session: AsyncSession) -> None:
    await _seed(session)
    student_id = await _first_student_id(session)

    items = await SqlAnalyticsRepository(session).recent_activity(student_id, limit=10)

    assert items
    ids = [item.id for item in items]
    assert ids == sorted(ids, reverse=True)
    assert all(item.student_id == student_id for item in items)


async def test_skill_levels_are_joined_to_names(session: AsyncSession) -> None:
    await _seed(session)
    student_id = await _first_student_id(session)

    pairs = await SqlAnalyticsRepository(session).skill_levels(student_id)

    assert pairs
    for skill, level in pairs:
        assert skill.code
        assert level.student_id == student_id
        assert Decimal(0) <= level.level <= _MAX_LEVEL


async def test_snapshot_until_filter(session: AsyncSession) -> None:
    await _seed(session)
    student_id = await _first_student_id(session)
    repository = SqlAnalyticsRepository(session)

    snapshots = await repository.daily_snapshots(student_id)
    cutoff = snapshots[len(snapshots) // 2].day
    filtered = await repository.daily_snapshots(student_id, until=cutoff)

    assert filtered
    assert all(snapshot.day <= cutoff for snapshot in filtered)
    assert len(filtered) <= len(snapshots)


async def test_campus_repository_get(session: AsyncSession) -> None:
    await _seed(session)
    repository = SqlCampusRepository(session)

    campus = await repository.get(1)
    assert campus is not None
    assert campus.code
    assert await repository.get(9999) is None
