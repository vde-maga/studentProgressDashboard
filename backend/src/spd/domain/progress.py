"""Pure progress computations.

Side-effect-free, total functions over progress data. They live in the domain
so they can be property-tested in isolation and reused by any layer without
touching persistence (see ADR 0003). ``level_for_xp`` is the canonical 42
level curve; the seeder and the analytics API both depend on it.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date
from decimal import Decimal
from itertools import pairwise

__all__ = [
    "MAX_LEVEL",
    "active_streak",
    "assign_ranks",
    "level_for_xp",
    "level_progress",
    "xp_for_level",
    "xp_velocity",
]

# 42 caps the level at 21; the curve below saturates here.
MAX_LEVEL = Decimal("21.00")
_HUNDRED = Decimal(100)
_CENTS = Decimal("0.01")
_BASIS_POINTS = Decimal("0.0001")


def level_for_xp(xp: int) -> Decimal:
    """42-style level curve: ``level = sqrt(xp / 100)``, capped at 21."""
    if xp <= 0:
        return Decimal("0.00")
    level = min(MAX_LEVEL, (Decimal(xp) / _HUNDRED).sqrt())
    return level.quantize(_CENTS)


def xp_for_level(level: Decimal) -> int:
    """Inverse of :func:`level_for_xp`: the XP that yields ``level``."""
    if level <= 0:
        return 0
    capped = min(Decimal(level), MAX_LEVEL)
    return int((capped * capped) * _HUNDRED)


def level_progress(xp: int) -> Decimal:
    """Fraction (0-1) of the way between the current and next whole level."""
    level = level_for_xp(xp)
    if level >= MAX_LEVEL:
        return Decimal("0.00")
    whole = Decimal(int(level))
    return (level - whole).quantize(_BASIS_POINTS)


def xp_velocity(snapshots: Sequence[object]) -> Decimal:
    """Average XP gained per day across snapshots ordered oldest-first.

    Returns ``0`` when there are fewer than two snapshots or they share a day.
    Accepts any objects exposing ``day`` and ``xp_total`` (duck-typed to stay
    free of an import cycle with the entities module).
    """
    if len(snapshots) < 2:
        return Decimal("0.00")
    first, last = snapshots[0], snapshots[-1]
    days = (last.day - first.day).days  # type: ignore[attr-defined]
    if days <= 0:
        return Decimal("0.00")
    gained = last.xp_total - first.xp_total  # type: ignore[attr-defined]
    return (Decimal(gained) / Decimal(days)).quantize(_CENTS)


def active_streak(days: Iterable[date]) -> int:
    """Length of the consecutive-day run ending at the latest given day."""
    ordered = sorted(set(days))
    if not ordered:
        return 0
    streak = 1
    for previous, current in pairwise(ordered):
        streak = streak + 1 if (current - previous).days == 1 else 1
    return streak


def assign_ranks(values: Sequence[int]) -> list[int]:
    """Competition ranking (1, 2, 2, 4): equal values share the better rank."""
    return [sum(1 for other in values if other > value) + 1 for value in values]
