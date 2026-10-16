"""Seeder integration tests: determinism and data integrity."""

import hashlib
from datetime import date, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from spd.domain.enums import ActivityKind
from spd.domain.progress import level_for_xp
from spd.infrastructure.db import models as orm
from spd.infrastructure.seed import SeedConfig, Seeder

pytestmark = pytest.mark.integration

_FIXED_END = date(2026, 10, 15)


async def _activity_signature(session: AsyncSession) -> str:
    result = await session.execute(
        select(
            orm.ActivityEvent.user_id,
            orm.ActivityEvent.kind,
            orm.ActivityEvent.day,
            orm.ActivityEvent.xp_delta,
            orm.ActivityEvent.project_id,
        ).order_by(orm.ActivityEvent.id)
    )
    payload = "\n".join(
        "|".join("" if value is None else str(value) for value in row)
        for row in result.all()
    )
    return hashlib.sha256(payload.encode()).hexdigest()


async def test_same_seed_produces_identical_rows(session: AsyncSession) -> None:
    config = SeedConfig(
        seed=1234, student_count=6, days=40, end_date=_FIXED_END, reset=True
    )

    await Seeder(config).run(session)
    first = await _activity_signature(session)

    await Seeder(config).run(session)
    second = await _activity_signature(session)

    assert first == second


async def test_different_seed_produces_different_rows(
    session: AsyncSession,
) -> None:
    def config(seed: int) -> SeedConfig:
        return SeedConfig(
            seed=seed,
            student_count=6,
            days=40,
            end_date=_FIXED_END,
            reset=True,
        )

    await Seeder(config(1)).run(session)
    first = await _activity_signature(session)

    await Seeder(config(2)).run(session)
    second = await _activity_signature(session)

    assert first != second


async def test_seeded_data_is_internally_consistent(
    session: AsyncSession,
) -> None:
    config = SeedConfig(
        seed=99, student_count=5, days=30, end_date=_FIXED_END, reset=True
    )
    await Seeder(config).run(session)

    students = await session.scalar(select(func.count()).select_from(orm.User))
    assert students == config.student_count

    every_snapshot_has_a_student = await session.scalar(
        select(func.count())
        .select_from(orm.DailySnapshot)
        .join(orm.User, orm.User.id == orm.DailySnapshot.user_id)
    )
    snapshots = await session.scalar(
        select(func.count()).select_from(orm.DailySnapshot)
    )
    assert every_snapshot_has_a_student == snapshots

    negative_levels = await session.scalar(
        select(func.count())
        .select_from(orm.DailySnapshot)
        .where(orm.DailySnapshot.level < 0)
    )
    assert negative_levels == 0


async def test_seed_advances_identity_sequences(session: AsyncSession) -> None:
    config = SeedConfig(
        seed=7, student_count=5, days=30, end_date=_FIXED_END, reset=True
    )
    await Seeder(config).run(session)

    highest = await session.scalar(select(func.max(orm.ActivityEvent.id)))

    student_id = await session.scalar(select(orm.User.id).limit(1))
    assert student_id is not None

    event = orm.ActivityEvent(
        user_id=student_id,
        kind=ActivityKind.COMMIT,
        day=_FIXED_END,
        xp_delta=150,
        occurred_at=datetime(2026, 10, 15, 12, 0),
        payload={},
    )
    session.add(event)
    await session.flush()

    assert event.id > (highest or 0)


def test_level_curve_is_monotonic_and_capped() -> None:
    assert level_for_xp(0) == 0
    assert level_for_xp(100) == 1
    assert level_for_xp(10_000) == 10
    assert level_for_xp(10_000_000) == 21
    previous = level_for_xp(0)
    for xp in range(0, 50_000, 500):
        current = level_for_xp(xp)
        assert current >= previous
        previous = current
