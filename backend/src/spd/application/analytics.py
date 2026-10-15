"""Read-side use-cases for progress analytics.

The service composes repository reads into the projection dataclasses the HTTP
layer serialises. It owns the business rules that turn raw rows into a profile
(rank, level progression, streak) and a ranked leaderboard.
"""

from __future__ import annotations

from datetime import date

from spd.core.errors import AppError
from spd.domain.entities import DailySnapshot, Student
from spd.domain.progress import (
    active_streak,
    assign_ranks,
    level_for_xp,
    level_progress,
)
from spd.domain.readmodels import (
    ActivityItem,
    CohortSummary,
    LeaderboardRow,
    SkillLevelView,
    StudentProfile,
    StudentProgress,
)
from spd.domain.repositories import (
    AnalyticsRepository,
    CampusRepository,
    CohortRepository,
    LeaderboardRepository,
    StudentRepository,
)

__all__ = ["AnalyticsService"]


class AnalyticsService:
    """Orchestrates reads into analytics read models."""

    def __init__(
        self,
        *,
        students: StudentRepository,
        campuses: CampusRepository,
        analytics: AnalyticsRepository,
        leaderboard: LeaderboardRepository,
        cohort: CohortRepository,
    ) -> None:
        self._students = students
        self._campuses = campuses
        self._analytics = analytics
        self._leaderboard = leaderboard
        self._cohort = cohort

    async def _require_student(self, login: str) -> Student:
        student = await self._students.get_by_login(login)
        if student is None:
            raise AppError(404, "student_not_found", f"No student named '{login}'.")
        return student

    async def _ranked(
        self,
    ) -> tuple[list[StudentProgress], list[int]]:
        """Return the ordered cohort plus the rank of each row."""
        progress = await self._leaderboard.ranked()
        ranks = assign_ranks([row.xp_total for row in progress])
        return progress, ranks

    async def student_profile(self, login: str) -> StudentProfile:
        """Build a student's profile with rank, level progress and streak."""
        student = await self._require_student(login)
        campus = await self._campuses.get(student.campus_id)
        if campus is None:
            raise AppError(
                500, "campus_missing", "The student's campus no longer exists."
            )
        snapshots = await self._analytics.daily_snapshots(student.id)
        xp_total = snapshots[-1].xp_total if snapshots else 0
        projects_done = snapshots[-1].projects_done if snapshots else 0
        progress, ranks = await self._ranked()
        rank = next(
            (
                ranks[index]
                for index, row in enumerate(progress)
                if row.student.id == student.id
            ),
            len(progress) + 1,
        )
        return StudentProfile(
            student=student,
            campus=campus,
            xp_total=xp_total,
            level=level_for_xp(xp_total),
            level_progress=level_progress(xp_total),
            projects_done=projects_done,
            rank=rank,
            current_streak=active_streak(snapshot.day for snapshot in snapshots),
        )

    async def student_progress(
        self,
        login: str,
        *,
        since: date | None = None,
        until: date | None = None,
    ) -> list[DailySnapshot]:
        """Return a student's progress time series within the given window."""
        student = await self._require_student(login)
        return await self._analytics.daily_snapshots(
            student.id, since=since, until=until
        )

    async def student_activity(self, login: str, *, limit: int) -> list[ActivityItem]:
        """Return a student's most recent activity, newest first."""
        student = await self._require_student(login)
        return await self._analytics.recent_activity(student.id, limit=limit)

    async def student_skills(self, login: str) -> list[SkillLevelView]:
        """Return a student's skills with their current levels."""
        student = await self._require_student(login)
        pairs = await self._analytics.skill_levels(student.id)
        return [
            SkillLevelView(code=skill.code, name=skill.name, level=level.level)
            for skill, level in pairs
        ]

    async def leaderboard(self, *, limit: int, offset: int) -> list[LeaderboardRow]:
        """Return a page of the ranked cohort leaderboard."""
        progress, ranks = await self._ranked()
        rows = [
            LeaderboardRow(
                rank=ranks[index],
                student=row.student,
                campus=row.campus,
                xp_total=row.xp_total,
                level=row.level,
                projects_done=row.projects_done,
            )
            for index, row in enumerate(progress)
        ]
        return rows[offset : offset + limit]

    async def cohort_summary(self) -> CohortSummary:
        """Return aggregate figures across the whole cohort."""
        return await self._cohort.summary()
