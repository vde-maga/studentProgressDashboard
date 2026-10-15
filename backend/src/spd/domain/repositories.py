"""Repository interfaces (ports) owned by the domain.

Implementations live in ``spd.infrastructure.repositories``. Depending on these
small ``Protocol``s — instead of concrete classes — keeps application code
independent of SQLAlchemy and lets tests substitute fast in-memory fakes
(Dependency Inversion + Interface Segregation).
"""

from datetime import date
from typing import Protocol

from spd.domain.entities import (
    Account,
    Campus,
    DailySnapshot,
    Skill,
    SkillLevel,
    Student,
)
from spd.domain.readmodels import (
    ActivityItem,
    CohortSummary,
    StudentProgress,
)

__all__ = [
    "AccountRepository",
    "AnalyticsRepository",
    "CampusRepository",
    "CohortRepository",
    "LeaderboardRepository",
    "StudentRepository",
]


class AccountRepository(Protocol):
    """Read access to authentication credentials."""

    async def find_by_login(self, login: str) -> Account | None:
        """Return the account with ``login`` (with its hash), or ``None``."""
        ...


class StudentRepository(Protocol):
    """Read access to student accounts."""

    async def get_by_login(self, login: str) -> Student | None:
        """Return the student with ``login``, or ``None`` if absent."""
        ...

    async def list_students(self, *, limit: int, offset: int) -> list[Student]:
        """Return a page of students ordered by login."""
        ...

    async def count(self) -> int:
        """Return the total number of students."""
        ...


class CampusRepository(Protocol):
    """Read access to campuses."""

    async def get(self, campus_id: int) -> Campus | None:
        """Return the campus with ``campus_id``, or ``None`` if absent."""
        ...


class AnalyticsRepository(Protocol):
    """Read access to a student's precomputed progress time series."""

    async def daily_snapshots(
        self,
        student_id: int,
        *,
        since: date | None = None,
        until: date | None = None,
    ) -> list[DailySnapshot]:
        """Return snapshots for a student, oldest first, within the window."""
        ...

    async def total_xp(self, student_id: int) -> int:
        """Return the latest known total XP for a student (0 if none)."""
        ...

    async def recent_activity(
        self, student_id: int, *, limit: int
    ) -> list[ActivityItem]:
        """Return a student's most recent activity items, newest first."""
        ...

    async def events_after(self, last_id: int, *, limit: int) -> list[ActivityItem]:
        """Return activity items with ``id > last_id``, oldest first."""
        ...

    async def latest_event_id(self) -> int:
        """Return the highest activity-event id, or 0 when there is none."""
        ...

    async def skill_levels(self, student_id: int) -> list[tuple[Skill, SkillLevel]]:
        """Return a student's skills paired with their current level."""
        ...


class LeaderboardRepository(Protocol):
    """Read access to the cohort ranking."""

    async def ranked(self) -> list[StudentProgress]:
        """Return every student's latest progress, highest XP first."""
        ...


class CohortRepository(Protocol):
    """Read access to cohort-wide aggregates."""

    async def summary(self) -> CohortSummary:
        """Return aggregate figures across the whole cohort."""
        ...
