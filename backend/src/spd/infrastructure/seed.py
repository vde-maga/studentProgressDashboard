"""Deterministic demo-data seeder.

Generates a reproducible cohort (same ``seed`` → identical rows) so demos and
screenshots are stable. All randomness flows through a seeded ``random.Random``
and a seeded Faker instance, and every timestamp is derived from a fixed
``end_date`` — nothing reads the wall clock. See docs/adr/0001.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from faker import Faker
from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from spd.core.config import get_settings
from spd.domain.enums import (
    ActivityKind,
    CursusKind,
    EnrollmentStatus,
    ProjectKind,
    Role,
)
from spd.infrastructure.db import models as orm
from spd.infrastructure.db.session import create_engine, create_session_factory

__all__ = ["SeedConfig", "Seeder"]

_ONE_DAY = timedelta(days=1)

# Rows per INSERT statement. Multi-row VALUES keep bulk seeding to one round
# trip per chunk instead of one per row (hundreds of times faster over a socket).
_INSERT_CHUNK = 1000

_CAMPUSES = [
    ("LIS", "42 Lisboa", "Lisboa", "PT"),
    ("PTO", "42 Porto", "Porto", "PT"),
    ("SAO", "42 São Paulo", "São Paulo", "BR"),
    ("PAR", "42 Paris", "Paris", "FR"),
]

_CURSUS = [
    ("42cursus", "42 Cursus", CursusKind.CURSUS),
    ("piscine", "Piscine", CursusKind.PISCINE),
]

_SKILLS = [
    ("c", "C"),
    ("cpp", "C++"),
    ("python", "Python"),
    ("go", "Go"),
    ("rust", "Rust"),
    ("web", "Web"),
    ("algorithms", "Algorithms"),
    ("oop", "Object-Oriented Programming"),
    ("sysadmin", "System Administration"),
    ("docker", "Docker"),
    ("sql", "SQL"),
    ("security", "Security"),
]

# (slug, name, difficulty, estimated_hours, kind) — ordered by difficulty.
_PROJECTS = [
    ("libft", "Libft", 1, 60, ProjectKind.INNER),
    ("get_next_line", "get_next_line", 1, 40, ProjectKind.INNER),
    ("exam00", "Exam 00", 1, 20, ProjectKind.EXAM),
    ("born2beroot", "Born2beroot", 2, 40, ProjectKind.OUTER),
    ("ft_printf", "ft_printf", 2, 60, ProjectKind.INNER),
    ("so_long", "so_long", 2, 60, ProjectKind.INNER),
    ("push_swap", "push_swap", 3, 80, ProjectKind.INNER),
    ("philosophers", "Philosophers", 3, 80, ProjectKind.INNER),
    ("libasm", "libasm", 3, 60, ProjectKind.INNER),
    ("minishell", "minishell", 4, 120, ProjectKind.INNER),
    ("cub3d", "cub3d", 4, 120, ProjectKind.INNER),
    ("inception", "Inception", 4, 100, ProjectKind.OUTER),
    ("cpp-modules", "C++ Modules", 4, 160, ProjectKind.INNER),
    ("netpractice", "NetPractice", 3, 20, ProjectKind.OUTER),
    ("webserv", "webserv", 5, 150, ProjectKind.INNER),
    ("ft_containers", "ft_containers", 5, 150, ProjectKind.INNER),
    ("ft_irc", "ft_irc", 5, 150, ProjectKind.INNER),
    ("exam02", "Exam 02", 5, 20, ProjectKind.EXAM),
    ("ft_transcendence", "ft_transcendence", 6, 200, ProjectKind.OUTER),
]

_HIGH_MARK = Decimal("100.00")
_MAX_LEVEL = Decimal("21.00")


@dataclass(frozen=True, slots=True)
class SeedConfig:
    """Knobs for a reproducible seed run."""

    seed: int = 42
    student_count: int = 60
    days: int = 365
    end_date: date = field(default_factory=date.today)
    reset: bool = True

    @property
    def start_date(self) -> date:
        return self.end_date - timedelta(days=self.days - 1)


def level_for_xp(xp: int) -> Decimal:
    """42-style level curve: level = sqrt(xp / 100), capped at 21."""
    if xp <= 0:
        return Decimal("0.00")
    level = min(_MAX_LEVEL, (Decimal(xp) / Decimal(100)).sqrt())
    return level.quantize(Decimal("0.01"))


class Seeder:
    """Populates the catalogue, cohort and progress time series."""

    def __init__(self, config: SeedConfig) -> None:
        self._config = config
        self._rng = random.Random(config.seed)
        self._faker = Faker()
        self._faker.seed_instance(config.seed)

    async def run(self, session: AsyncSession) -> None:
        if self._config.reset:
            await self._truncate(session)

        campus_ids = await self._seed_catalogue(session)
        student_ids = await self._seed_users(session, campus_ids)
        project_ids = list(range(1, len(_PROJECTS) + 1))
        finishes, finished_enrollments = await self._seed_enrollments(
            session, student_ids, project_ids
        )
        await self._seed_audits(session, student_ids, finished_enrollments)
        await self._seed_activity(session, student_ids, project_ids, finishes)
        await session.commit()

    @staticmethod
    async def _bulk_insert(
        session: AsyncSession,
        model: type[DeclarativeBase],
        rows: list[dict[str, object]],
    ) -> None:
        """Insert rows in chunked multi-row VALUES statements."""
        for start in range(0, len(rows), _INSERT_CHUNK):
            chunk = rows[start : start + _INSERT_CHUNK]
            await session.execute(insert(model).values(chunk))

    async def _truncate(self, session: AsyncSession) -> None:
        tables = [
            orm.DailySnapshot,
            orm.ActivityEvent,
            orm.Audit,
            orm.Enrollment,
            orm.SkillLevel,
            orm.User,
            orm.Project,
            orm.Skill,
            orm.Cursus,
            orm.Campus,
        ]
        for table in tables:
            await session.execute(delete(table))
        await session.commit()

    async def _seed_catalogue(self, session: AsyncSession) -> list[int]:
        await session.execute(
            insert(orm.Campus),
            [
                {"id": i, "code": code, "name": name, "city": city, "country": country}
                for i, (code, name, city, country) in enumerate(_CAMPUSES, start=1)
            ],
        )
        await session.execute(
            insert(orm.Cursus),
            [
                {"id": i, "code": code, "name": name, "kind": kind.value}
                for i, (code, name, kind) in enumerate(_CURSUS, start=1)
            ],
        )
        await session.execute(
            insert(orm.Skill),
            [
                {"id": i, "code": code, "name": name}
                for i, (code, name) in enumerate(_SKILLS, start=1)
            ],
        )
        await session.execute(
            insert(orm.Project),
            [
                {
                    "id": i,
                    "slug": slug,
                    "name": name,
                    "difficulty": difficulty,
                    "estimated_hours": hours,
                    "kind": kind.value,
                    "cursus_id": 1,
                }
                for i, (slug, name, difficulty, hours, kind) in enumerate(
                    _PROJECTS, start=1
                )
            ],
        )
        await session.flush()
        return list(range(1, len(_CAMPUSES) + 1))

    async def _seed_users(
        self, session: AsyncSession, campus_ids: list[int]
    ) -> list[int]:
        rows: list[dict[str, object]] = []
        logins: set[str] = set()
        start = self._config.start_date
        for user_id in range(1, self._config.student_count + 1):
            login = self._unique_login(logins)
            joined = start + timedelta(
                days=self._rng.randint(0, self._config.days // 2)
            )
            blackholed = (
                joined + timedelta(days=self._rng.randint(30, 120))
                if self._rng.random() < 0.08
                else None
            )
            rows.append(
                {
                    "id": user_id,
                    "login": login,
                    "email": f"{login}@student.42.fr",
                    "full_name": self._faker.name(),
                    "role": Role.STUDENT.value,
                    "campus_id": self._rng.choice(campus_ids),
                    "blackholed_at": blackholed,
                    "created_at": _at(joined, self._rng),
                    "updated_at": _at(joined, self._rng),
                }
            )
        await self._bulk_insert(session, orm.User, rows)
        await session.flush()
        return [user_id for user_id in range(1, self._config.student_count + 1)]

    async def _seed_enrollments(
        self, session: AsyncSession, student_ids: list[int], project_ids: list[int]
    ) -> tuple[dict[int, list[tuple[date, int]]], list[int]]:
        """Insert enrollments.

        Returns, per student, the ``(finish_date, mark)`` pairs and the ids of
        the finished enrollments (used later for audits).
        """
        rows: list[dict[str, object]] = []
        finishes: dict[int, list[tuple[date, int]]] = {sid: [] for sid in student_ids}
        finished_enrollments: list[int] = []
        enrollment_id = 1
        start = self._config.start_date
        for student_id in student_ids:
            capacity = self._rng.randint(3, len(project_ids))
            cursor = start + timedelta(days=self._rng.randint(0, 30))
            for offset, project_id in enumerate(project_ids[:capacity]):
                if cursor > self._config.end_date:
                    break
                started = cursor
                finished_at = started + timedelta(days=self._rng.randint(5, 21))
                if finished_at > self._config.end_date or (
                    offset == capacity - 1 and self._rng.random() < 0.4
                ):
                    status = EnrollmentStatus.IN_PROGRESS
                elif self._rng.random() < 0.15:
                    status = EnrollmentStatus.FAILED
                else:
                    status = EnrollmentStatus.FINISHED
                mark = self._mark(status)
                row_finished = (
                    _at(finished_at, self._rng)
                    if status is not EnrollmentStatus.IN_PROGRESS
                    else None
                )
                rows.append(
                    {
                        "id": enrollment_id,
                        "user_id": student_id,
                        "project_id": project_id,
                        "status": status.value,
                        "final_mark": mark,
                        "attempt": 1,
                        "started_at": _at(started, self._rng),
                        "finished_at": row_finished,
                        "created_at": _at(started, self._rng),
                        "updated_at": _at(started, self._rng),
                    }
                )
                if status is EnrollmentStatus.FINISHED and mark is not None:
                    finishes[student_id].append((finished_at, mark))
                    finished_enrollments.append(enrollment_id)
                enrollment_id += 1
                cursor = finished_at + timedelta(days=self._rng.randint(1, 10))
        await self._bulk_insert(session, orm.Enrollment, rows)
        await session.flush()
        return finishes, finished_enrollments

    async def _seed_audits(
        self,
        session: AsyncSession,
        student_ids: list[int],
        finished_enrollments: list[int],
    ) -> None:
        rows: list[dict[str, object]] = []
        audit_id = 1
        for enrollment_id in finished_enrollments:
            for corrector_id in self._rng.sample(
                student_ids, k=self._rng.randint(1, 2)
            ):
                rows.append(
                    {
                        "id": audit_id,
                        "enrollment_id": enrollment_id,
                        "corrector_id": corrector_id,
                        "grade": self._rng.randint(50, 125),
                        "comment": (
                            self._faker.sentence() if self._rng.random() < 0.3 else None
                        ),
                        "created_at": _at(self._config.end_date, self._rng),
                    }
                )
                audit_id += 1
        if rows:
            await self._bulk_insert(session, orm.Audit, rows)
            await session.flush()

    async def _seed_activity(
        self,
        session: AsyncSession,
        student_ids: list[int],
        project_ids: list[int],
        finishes: dict[int, list[tuple[date, int]]],
    ) -> None:
        event_rows: list[dict[str, object]] = []
        snapshot_rows: list[dict[str, object]] = []
        event_id = 1
        end = self._config.end_date
        for student_id in student_ids:
            xp_by_day: dict[date, int] = {}
            project_done_by_day: dict[date, int] = {}
            day = self._config.start_date + timedelta(days=self._rng.randint(0, 30))
            while day <= end:
                if self._rng.random() < (0.3 if day.weekday() >= 5 else 0.65):
                    for kind, xp, project_id in self._day_events(project_ids):
                        event_rows.append(
                            {
                                "id": event_id,
                                "user_id": student_id,
                                "kind": kind.value,
                                "day": day,
                                "xp_delta": xp,
                                "project_id": project_id,
                                "occurred_at": _at(day, self._rng),
                                "payload": {},
                            }
                        )
                        event_id += 1
                        xp_by_day[day] = xp_by_day.get(day, 0) + xp
                day += _ONE_DAY

            for finish_day, mark in finishes[student_id]:
                if finish_day > end:
                    continue
                event_rows.append(
                    {
                        "id": event_id,
                        "user_id": student_id,
                        "kind": ActivityKind.PROJECT_VALIDATED.value,
                        "day": finish_day,
                        "xp_delta": mark,
                        "project_id": None,
                        "occurred_at": _at(finish_day, self._rng),
                        "payload": {},
                    }
                )
                event_id += 1
                xp_by_day[finish_day] = xp_by_day.get(finish_day, 0) + mark
                project_done_by_day[finish_day] = (
                    project_done_by_day.get(finish_day, 0) + 1
                )

            snapshot_rows.extend(
                self._snapshots_for(student_id, xp_by_day, project_done_by_day)
            )

        await self._bulk_insert(session, orm.ActivityEvent, event_rows)
        await self._bulk_insert(session, orm.DailySnapshot, snapshot_rows)
        await session.flush()

    def _snapshots_for(
        self,
        student_id: int,
        xp_by_day: dict[date, int],
        project_done_by_day: dict[date, int],
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        cumulative_xp = 0
        cumulative_projects = 0
        for day in sorted(xp_by_day):
            cumulative_xp += xp_by_day[day]
            cumulative_projects += project_done_by_day.get(day, 0)
            rows.append(
                {
                    "user_id": student_id,
                    "day": day,
                    "xp_total": cumulative_xp,
                    "level": level_for_xp(cumulative_xp),
                    "projects_done": cumulative_projects,
                }
            )
        return rows

    def _day_events(
        self, project_ids: list[int]
    ) -> list[tuple[ActivityKind, int, int | None]]:
        events: list[tuple[ActivityKind, int, int | None]] = [
            (ActivityKind.LOGIN, 0, None)
        ]
        for _ in range(self._rng.randint(0, 2)):
            events.append(
                (
                    ActivityKind.COMMIT,
                    self._rng.randint(5, 25),
                    self._rng.choice(project_ids),
                )
            )
        if self._rng.random() < 0.2:
            events.append((ActivityKind.EVALUATION_GIVEN, 10, None))
        if self._rng.random() < 0.2:
            events.append((ActivityKind.EVALUATION_RECEIVED, 10, None))
        return events

    def _mark(self, status: EnrollmentStatus) -> int | None:
        if status is EnrollmentStatus.FINISHED:
            return self._rng.randint(80, 125)
        if status is EnrollmentStatus.FAILED:
            return self._rng.randint(0, 75)
        return None

    def _unique_login(self, seen: set[str]) -> str:
        while True:
            login = "".join(
                ch for ch in self._faker.user_name().lower() if ch.isalnum()
            )[:12]
            if login and login not in seen:
                seen.add(login)
                return login


def _at(day: date, rng: random.Random) -> datetime:
    """Spread a timestamp across a working day, always timezone-aware (UTC)."""
    return datetime.combine(
        day,
        time(hour=rng.randint(7, 23), minute=rng.randint(0, 59)),
        tzinfo=UTC,
    )


async def _main() -> None:
    settings = get_settings()
    engine = create_engine(settings)
    factory = create_session_factory(engine)
    async with factory() as session:
        await Seeder(SeedConfig()).run(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
