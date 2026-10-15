"""SQLAlchemy models for the progress domain.

Pure persistence concerns live here; the domain-facing shape of each row is
produced by ``spd.infrastructure.mappers``. Relationships are intentionally
omitted: async code always issues explicit queries instead of triggering lazy
loads (see ADR 0001).
"""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from spd.domain.enums import (
    ActivityKind,
    CursusKind,
    EnrollmentStatus,
    ProjectKind,
    Role,
)
from spd.infrastructure.db.base import Base, TimestampMixin

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
    "User",
]


def _enum(enum_type: type[StrEnum]) -> SAEnum:
    """Return a portable VARCHAR enum (never a native PostgreSQL enum)."""
    return SAEnum(
        enum_type,
        native_enum=False,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
    )


def _enum_check(column: str, enum_type: type[StrEnum], name: str) -> CheckConstraint:
    """Build the database-level CHECK constraint for a portable enum column.

    Kept explicit (instead of ``Enum(create_constraint=True)``) so the naming
    convention yields exactly one constraint and Alembic renders it once.
    """
    allowed = ", ".join(f"'{member.value}'" for member in enum_type)
    return CheckConstraint(f"{column} IN ({allowed})", name=name)


class Campus(TimestampMixin, Base):
    """A physical 42 campus."""

    __tablename__ = "campuses"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    city: Mapped[str] = mapped_column(String(64))
    country: Mapped[str] = mapped_column(String(2))


class Cursus(TimestampMixin, Base):
    """A curriculum."""

    __tablename__ = "cursus"
    __table_args__ = (_enum_check("kind", CursusKind, "cursus_kind"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    kind: Mapped[CursusKind] = mapped_column(_enum(CursusKind))


class Skill(TimestampMixin, Base):
    """A skill students gain experience in."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(64))


class Project(TimestampMixin, Base):
    """A project belonging to a cursus."""

    __tablename__ = "projects"
    __table_args__ = (
        _enum_check("kind", ProjectKind, "project_kind"),
        CheckConstraint("difficulty BETWEEN 1 AND 10", name="difficulty_range"),
        CheckConstraint("estimated_hours > 0", name="estimated_hours_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    difficulty: Mapped[int] = mapped_column(SmallInteger)
    estimated_hours: Mapped[int] = mapped_column(Integer)
    kind: Mapped[ProjectKind] = mapped_column(_enum(ProjectKind))
    cursus_id: Mapped[int] = mapped_column(
        ForeignKey("cursus.id", ondelete="RESTRICT"), index=True
    )


class User(TimestampMixin, Base):
    """An account; students produce the progress data."""

    __tablename__ = "users"
    __table_args__ = (_enum_check("role", Role, "role"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    login: Mapped[str] = mapped_column(String(32), unique=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    full_name: Mapped[str] = mapped_column(String(128))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(_enum(Role), server_default=Role.STUDENT.value)
    campus_id: Mapped[int] = mapped_column(
        ForeignKey("campuses.id", ondelete="RESTRICT"), index=True
    )
    blackholed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Enrollment(TimestampMixin, Base):
    """A single attempt at a project."""

    __tablename__ = "enrollments"
    __table_args__ = (
        _enum_check("status", EnrollmentStatus, "enrollment_status"),
        CheckConstraint("attempt > 0", name="attempt_positive"),
        CheckConstraint(
            "final_mark IS NULL OR final_mark BETWEEN 0 AND 125",
            name="final_mark_range",
        ),
        UniqueConstraint("user_id", "project_id", "attempt"),
        Index("ix_enrollments_user_id_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[EnrollmentStatus] = mapped_column(_enum(EnrollmentStatus))
    final_mark: Mapped[int | None] = mapped_column(SmallInteger)
    attempt: Mapped[int] = mapped_column(SmallInteger, server_default="1")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Audit(Base):
    """A peer evaluation performed on an enrollment."""

    __tablename__ = "audits"
    __table_args__ = (
        CheckConstraint("grade BETWEEN 0 AND 125", name="grade_range"),
        UniqueConstraint("enrollment_id", "corrector_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(
        ForeignKey("enrollments.id", ondelete="CASCADE")
    )
    corrector_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    grade: Mapped[int] = mapped_column(SmallInteger)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SkillLevel(Base):
    """A student's current level in a skill."""

    __tablename__ = "skill_levels"
    __table_args__ = (CheckConstraint("level BETWEEN 0 AND 21", name="level_range"),)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    level: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ActivityEvent(Base):
    """An atomic event on a student's timeline."""

    __tablename__ = "activity_events"
    __table_args__ = (
        _enum_check("kind", ActivityKind, "activity_kind"),
        Index(
            "ix_activity_events_user_id_day",
            "user_id",
            "day",
            postgresql_using="btree",
        ),
        Index("ix_activity_events_day", "day"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[ActivityKind] = mapped_column(_enum(ActivityKind))
    day: Mapped[date] = mapped_column(Date)
    xp_delta: Mapped[int] = mapped_column(Integer, server_default="0")
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL")
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default="{}", default=dict
    )


class DailySnapshot(Base):
    """A per-day rollup of a student's progress."""

    __tablename__ = "daily_snapshots"
    __table_args__ = (
        CheckConstraint("xp_total >= 0", name="xp_total_non_negative"),
        CheckConstraint("level BETWEEN 0 AND 21", name="level_range"),
        CheckConstraint("projects_done >= 0", name="projects_done_non_negative"),
        Index("ix_daily_snapshots_day", "day"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    xp_total: Mapped[int] = mapped_column(Integer)
    level: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    projects_done: Mapped[int] = mapped_column(Integer, server_default="0")
