"""Read models returned by the analytics queries.

These frozen dataclasses are persistence-agnostic projections shared by the
application layer and the repository ports. They are deliberately distinct
from the core entities: they carry only the fields a read endpoint needs.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from spd.domain.entities import Campus, Student
from spd.domain.enums import ActivityKind

__all__ = [
    "ActivityItem",
    "CohortSummary",
    "LeaderboardRow",
    "SkillLevelView",
    "StudentProfile",
    "StudentProgress",
]


@dataclass(frozen=True, slots=True)
class StudentProgress:
    """A student's latest progress figures, without any ranking applied."""

    student: Student
    campus: Campus
    xp_total: int
    level: Decimal
    projects_done: int


@dataclass(frozen=True, slots=True)
class StudentProfile:
    """A student's profile enriched with rank and level progression."""

    student: Student
    campus: Campus
    xp_total: int
    level: Decimal
    level_progress: Decimal
    projects_done: int
    rank: int
    current_streak: int


@dataclass(frozen=True, slots=True)
class LeaderboardRow:
    """One ranked row of the cohort leaderboard."""

    rank: int
    student: Student
    campus: Campus
    xp_total: int
    level: Decimal
    projects_done: int


@dataclass(frozen=True, slots=True)
class SkillLevelView:
    """A named skill and the student's current level in it."""

    code: str
    name: str
    level: Decimal


@dataclass(frozen=True, slots=True)
class ActivityItem:
    """An activity event projected for the timeline feed."""

    id: int
    student_id: int
    student_login: str
    kind: ActivityKind
    day: date
    xp_delta: int
    project_slug: str | None
    occurred_at: datetime
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class CohortSummary:
    """Aggregate figures across the whole cohort."""

    student_count: int
    total_xp: int
    average_level: Decimal
    projects_done: int
    active_last_7_days: int
