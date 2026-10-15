"""Persistence-agnostic domain entities.

These frozen dataclasses are the vocabulary shared by the application and
infrastructure layers. They deliberately carry no ORM or validation concern;
the SQLAlchemy models in ``spd.infrastructure.db.models`` are mapped to these
entities (and back) by ``spd.infrastructure.mappers``.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from spd.domain.enums import (
    ActivityKind,
    CursusKind,
    EnrollmentStatus,
    ProjectKind,
    Role,
)

__all__ = [
    "ActivityEvent",
    "Audit",
    "Campus",
    "Cursus",
    "DailySnapshot",
    "Enrollment",
    "Project",
    "Skill",
    "SkillLevel",
    "Student",
]

Id = int


@dataclass(frozen=True, slots=True)
class Campus:
    """A physical 42 campus."""

    id: Id
    code: str
    name: str
    city: str
    country: str


@dataclass(frozen=True, slots=True)
class Cursus:
    """A curriculum (e.g. the 42cursus or a piscine)."""

    id: Id
    code: str
    name: str
    kind: CursusKind


@dataclass(frozen=True, slots=True)
class Skill:
    """A skill students gain experience in."""

    id: Id
    code: str
    name: str


@dataclass(frozen=True, slots=True)
class Project:
    """A project belonging to a cursus."""

    id: Id
    slug: str
    name: str
    difficulty: int
    estimated_hours: int
    kind: ProjectKind
    cursus_id: Id


@dataclass(frozen=True, slots=True)
class Student:
    """A user account with student progress data."""

    id: Id
    login: str
    email: str
    full_name: str
    role: Role
    campus_id: Id
    blackholed_at: datetime | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Enrollment:
    """A single attempt at a project."""

    id: Id
    student_id: Id
    project_id: Id
    status: EnrollmentStatus
    final_mark: int | None
    attempt: int
    started_at: datetime
    finished_at: datetime | None


@dataclass(frozen=True, slots=True)
class Audit:
    """A peer evaluation performed on an enrollment."""

    id: Id
    enrollment_id: Id
    corrector_id: Id
    grade: int
    comment: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SkillLevel:
    """A student's current level in a skill."""

    student_id: Id
    skill_id: Id
    level: Decimal
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ActivityEvent:
    """An atomic event on a student's timeline."""

    id: Id
    student_id: Id
    kind: ActivityKind
    day: date
    xp_delta: int
    project_id: Id | None
    occurred_at: datetime
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class DailySnapshot:
    """A per-day rollup of a student's progress, precomputed for charts."""

    student_id: Id
    day: date
    xp_total: int
    level: Decimal
    projects_done: int
