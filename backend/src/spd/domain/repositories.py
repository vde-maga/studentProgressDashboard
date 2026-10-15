"""Repository interfaces (ports) owned by the domain.

Implementations live in ``spd.infrastructure.repositories``. Depending on these
small ``Protocol``s — instead of concrete classes — keeps application code
independent of SQLAlchemy and lets tests substitute fast in-memory fakes
(Dependency Inversion + Interface Segregation).
"""

from datetime import date
from typing import Protocol

from spd.domain.entities import DailySnapshot, Student

__all__ = ["AnalyticsRepository", "StudentRepository"]


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


class AnalyticsRepository(Protocol):
    """Read access to precomputed progress time series."""

    async def daily_snapshots(
        self, student_id: int, *, since: date | None = None
    ) -> list[DailySnapshot]:
        """Return snapshots for a student, oldest first, optionally since a day."""
        ...

    async def total_xp(self, student_id: int) -> int:
        """Return the latest known total XP for a student (0 if none)."""
        ...
