"""In-memory fakes for the domain repository ports.

Shared by the analytics service and HTTP tests so the analytics behaviour can
be exercised without a database.
"""

from datetime import UTC, date, datetime
from decimal import Decimal

from spd.domain.entities import (
    Campus,
    DailySnapshot,
    Skill,
    SkillLevel,
    Student,
)
from spd.domain.enums import ActivityKind, Role
from spd.domain.readmodels import (
    ActivityItem,
    CohortSummary,
    StudentProgress,
)

CAMPUS = Campus(id=1, code="LIS", name="42 Lisboa", city="Lisboa", country="PT")

ALICE = Student(
    id=1,
    login="alice",
    email="alice@student.42.fr",
    full_name="Alice Adams",
    role=Role.STUDENT,
    campus_id=1,
    blackholed_at=None,
    created_at=datetime(2026, 1, 1, tzinfo=UTC),
)

BOB = Student(
    id=2,
    login="bob",
    email="bob@student.42.fr",
    full_name="Bob Brown",
    role=Role.STUDENT,
    campus_id=1,
    blackholed_at=None,
    created_at=datetime(2026, 1, 2, tzinfo=UTC),
)


def _snapshot(day: int, xp: int, level: str, projects: int) -> DailySnapshot:
    return DailySnapshot(
        student_id=1,
        day=date(2026, 1, day),
        xp_total=xp,
        level=Decimal(level),
        projects_done=projects,
    )


_ALICE_SNAPSHOTS = [
    _snapshot(1, 100, "1.00", 1),
    _snapshot(2, 250, "1.58", 2),
    _snapshot(3, 400, "2.00", 3),
]

# Bob shares the day/xp/level/projects shape but has a different id.
_BOB_SNAPSHOTS = [
    DailySnapshot(
        student_id=2,
        day=date(2026, 1, 1),
        xp_total=100,
        level=Decimal("1.00"),
        projects_done=1,
    )
]

_ALICE_ACTIVITY = [
    ActivityItem(
        id=3,
        student_id=1,
        student_login="alice",
        kind=ActivityKind.PROJECT_VALIDATED,
        day=date(2026, 1, 3),
        xp_delta=100,
        project_slug="push_swap",
        occurred_at=datetime(2026, 1, 3, 10, tzinfo=UTC),
        payload={},
    ),
    ActivityItem(
        id=1,
        student_id=1,
        student_login="alice",
        kind=ActivityKind.LOGIN,
        day=date(2026, 1, 1),
        xp_delta=0,
        project_slug=None,
        occurred_at=datetime(2026, 1, 1, 8, tzinfo=UTC),
        payload={},
    ),
]

_SKILL_C = Skill(id=1, code="c", name="C")


class FakeStudentRepository:
    """In-memory student lookup."""

    def __init__(self, students: list[Student]) -> None:
        self._students = students

    async def get_by_login(self, login: str) -> Student | None:
        return next((s for s in self._students if s.login == login), None)

    async def list_students(self, *, limit: int, offset: int) -> list[Student]:
        return sorted(self._students, key=lambda s: s.login)[offset : offset + limit]

    async def count(self) -> int:
        return len(self._students)


class FakeCampusRepository:
    """In-memory campus lookup."""

    def __init__(self, campuses: list[Campus]) -> None:
        self._campuses = {campus.id: campus for campus in campuses}

    async def get(self, campus_id: int) -> Campus | None:
        return self._campuses.get(campus_id)


class FakeAnalyticsRepository:
    """In-memory progress reads."""

    def __init__(
        self,
        snapshots: dict[int, list[DailySnapshot]],
        activity: dict[int, list[ActivityItem]],
        skills: dict[int, list[tuple[Skill, SkillLevel]]],
    ) -> None:
        self._snapshots = snapshots
        self._activity = activity
        self._skills = skills

    async def daily_snapshots(
        self,
        student_id: int,
        *,
        since: date | None = None,
        until: date | None = None,
    ) -> list[DailySnapshot]:
        rows = self._snapshots.get(student_id, [])
        return [
            snap
            for snap in rows
            if (since is None or snap.day >= since)
            and (until is None or snap.day <= until)
        ]

    async def total_xp(self, student_id: int) -> int:
        rows = self._snapshots.get(student_id, [])
        return rows[-1].xp_total if rows else 0

    async def recent_activity(
        self, student_id: int, *, limit: int
    ) -> list[ActivityItem]:
        return sorted(
            self._activity.get(student_id, []), key=lambda item: item.id, reverse=True
        )[:limit]

    async def events_after(self, last_id: int, *, limit: int) -> list[ActivityItem]:
        items = [
            item
            for items in self._activity.values()
            for item in items
            if item.id > last_id
        ]
        return sorted(items, key=lambda item: item.id)[:limit]

    async def latest_event_id(self) -> int:
        return max(
            (item.id for items in self._activity.values() for item in items),
            default=0,
        )

    async def skill_levels(self, student_id: int) -> list[tuple[Skill, SkillLevel]]:
        return self._skills.get(student_id, [])


class FakeLeaderboardRepository:
    """In-memory cohort ranking."""

    def __init__(self, rows: list[StudentProgress]) -> None:
        self._rows = rows

    async def ranked(self) -> list[StudentProgress]:
        return list(self._rows)


class FakeCohortRepository:
    """In-memory cohort aggregates."""

    def __init__(self, summary: CohortSummary) -> None:
        self._summary = summary

    async def summary(self) -> CohortSummary:
        return self._summary


class FakeBackend:
    """A bundle of the fake repositories with sample data."""

    def __init__(self) -> None:
        alice = StudentProgress(
            student=ALICE,
            campus=CAMPUS,
            xp_total=400,
            level=Decimal("2.00"),
            projects_done=3,
        )
        bob = StudentProgress(
            student=BOB,
            campus=CAMPUS,
            xp_total=100,
            level=Decimal("1.00"),
            projects_done=1,
        )
        self.students = FakeStudentRepository([ALICE, BOB])
        self.campuses = FakeCampusRepository([CAMPUS])
        self.analytics = FakeAnalyticsRepository(
            snapshots={1: _ALICE_SNAPSHOTS, 2: _BOB_SNAPSHOTS},
            activity={1: _ALICE_ACTIVITY},
            skills={
                1: [
                    (
                        _SKILL_C,
                        SkillLevel(
                            student_id=1,
                            skill_id=1,
                            level=Decimal("3.50"),
                            updated_at=datetime(2026, 1, 3, tzinfo=UTC),
                        ),
                    )
                ]
            },
        )
        self.leaderboard = FakeLeaderboardRepository([alice, bob])
        self.cohort = FakeCohortRepository(
            CohortSummary(
                student_count=2,
                total_xp=500,
                average_level=Decimal("1.50"),
                projects_done=4,
                active_last_7_days=2,
            )
        )
