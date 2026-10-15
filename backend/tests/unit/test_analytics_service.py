"""Unit tests for the analytics use-cases, using in-memory fakes."""

from datetime import date
from decimal import Decimal

import pytest

from spd.application.analytics import AnalyticsService
from spd.core.errors import AppError
from tests.fakes import FakeBackend


def _service(backend: FakeBackend) -> AnalyticsService:
    return AnalyticsService(
        students=backend.students,
        campuses=backend.campuses,
        analytics=backend.analytics,
        leaderboard=backend.leaderboard,
        cohort=backend.cohort,
    )


async def test_profile_enriches_progress_with_rank_and_streak() -> None:
    profile = await _service(FakeBackend()).student_profile("alice")

    assert profile.student.login == "alice"
    assert profile.campus.code == "LIS"
    assert profile.xp_total == 400
    assert profile.level == Decimal("2.00")
    assert profile.level_progress == Decimal("0.0000")
    assert profile.projects_done == 3
    assert profile.rank == 1
    assert profile.current_streak == 3


async def test_profile_for_unknown_student_raises_not_found() -> None:
    with pytest.raises(AppError) as excinfo:
        await _service(FakeBackend()).student_profile("ghost")

    assert excinfo.value.status_code == 404
    assert excinfo.value.code == "student_not_found"


async def test_profile_without_snapshots_starts_at_zero() -> None:
    backend = FakeBackend()
    profile = await _service(backend).student_profile("bob")
    # Bob has a single snapshot, so his streak is one.
    assert profile.current_streak == 1
    assert profile.rank == 2


async def test_leaderboard_paginates_and_ranks() -> None:
    service = _service(FakeBackend())

    page = await service.leaderboard(limit=1, offset=0)
    assert [row.student.login for row in page] == ["alice"]
    assert page[0].rank == 1

    second = await service.leaderboard(limit=1, offset=1)
    assert [row.student.login for row in second] == ["bob"]
    assert second[0].rank == 2


async def test_progress_respects_the_window() -> None:
    service = _service(FakeBackend())

    points = await service.student_progress(
        "alice", since=date(2026, 1, 2), until=date(2026, 1, 3)
    )

    assert [point.day for point in points] == [date(2026, 1, 2), date(2026, 1, 3)]


async def test_activity_is_newest_first_and_limited() -> None:
    service = _service(FakeBackend())

    items = await service.student_activity("alice", limit=1)

    assert [item.id for item in items] == [3]


async def test_skills_are_named() -> None:
    service = _service(FakeBackend())

    skills = await service.student_skills("alice")

    assert len(skills) == 1
    assert skills[0].code == "c"
    assert skills[0].name == "C"
    assert skills[0].level == Decimal("3.50")


async def test_cohort_summary_is_returned() -> None:
    summary = await _service(FakeBackend()).cohort_summary()

    assert summary.student_count == 2
    assert summary.total_xp == 500
    assert summary.active_last_7_days == 2
