"""Property-based tests for the pure progress domain (hypothesis)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from spd.domain.entities import DailySnapshot
from spd.domain.progress import (
    MAX_LEVEL,
    active_streak,
    assign_ranks,
    level_for_xp,
    level_progress,
    xp_for_level,
    xp_velocity,
)

xp_values = st.integers(min_value=0, max_value=10_000_000)
levels = st.decimals(
    min_value=Decimal(0),
    max_value=MAX_LEVEL,
    allow_nan=False,
    allow_infinity=False,
    places=2,
)


@given(st.integers())
def test_level_is_zero_for_non_positive_xp(xp: int) -> None:
    if xp <= 0:
        assert level_for_xp(xp) == 0


@given(xp_values)
def test_level_stays_within_bounds(xp: int) -> None:
    assert 0 <= level_for_xp(xp) <= MAX_LEVEL


@given(xp_values, xp_values)
def test_level_is_monotonic(left: int, right: int) -> None:
    low, high = sorted((left, right))
    assert level_for_xp(low) <= level_for_xp(high)


@given(levels)
def test_xp_for_level_round_trips(level: Decimal) -> None:
    xp = xp_for_level(level)
    assert xp >= 0
    assert level_for_xp(xp) <= level
    # Round-tripping loses at most the integer truncation at the boundary.
    assert level - level_for_xp(xp) <= Decimal("0.12")


@given(xp_values)
def test_level_progress_is_a_fraction(xp: int) -> None:
    assert 0 <= level_progress(xp) < 1


@st.composite
def ordered_snapshots(draw: st.DrawFn) -> list[DailySnapshot]:
    count = draw(st.integers(min_value=2, max_value=10))
    start = draw(st.dates())
    xps = sorted(draw(st.lists(xp_values, min_size=count, max_size=count)))
    return [
        DailySnapshot(
            student_id=2,
            day=start + timedelta(days=index),
            xp_total=xp,
            level=level_for_xp(xp),
            projects_done=0,
        )
        for index, xp in enumerate(xps)
    ]


@given(ordered_snapshots())
def test_velocity_is_never_negative(snapshots: list[DailySnapshot]) -> None:
    assert xp_velocity(snapshots) >= 0


def test_velocity_needs_at_least_two_points() -> None:
    assert xp_velocity([]) == 0
    assert xp_velocity([DailySnapshot(1, date(2026, 1, 1), 100, Decimal("1"), 0)]) == 0


@given(st.sets(st.dates()))
def test_streak_is_bounded_by_the_days(days: set[date]) -> None:
    streak = active_streak(days)
    assert 0 <= streak <= len(days)


@given(st.dates(), st.integers(min_value=1, max_value=50))
def test_streak_of_a_contiguous_run(start: date, length: int) -> None:
    days = [start + timedelta(days=offset) for offset in range(length)]
    assert active_streak(days) == length


def test_streak_resets_after_a_gap() -> None:
    days = [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 5)]
    assert active_streak(days) == 1


@given(st.lists(st.integers(min_value=0, max_value=10_000), min_size=1, max_size=20))
def test_ranks_are_consistent(values: list[int]) -> None:
    ranks = assign_ranks(values)
    assert len(ranks) == len(values)
    assert min(ranks) == 1
    assert max(values) in values
    for i, left in enumerate(values):
        for j, right in enumerate(values):
            if left == right:
                assert ranks[i] == ranks[j]
            elif left > right:
                assert ranks[i] < ranks[j]


def test_competition_ranking_skips_positions() -> None:
    assert assign_ranks([10, 10, 5, 1]) == [1, 1, 3, 4]


@pytest.mark.parametrize(
    ("xp", "expected"),
    [(0, "0.00"), (100, "1.00"), (10_000, "10.00"), (10_000_000, "21.00")],
)
def test_level_curve_reference_points(xp: int, expected: str) -> None:
    assert level_for_xp(xp) == Decimal(expected)
