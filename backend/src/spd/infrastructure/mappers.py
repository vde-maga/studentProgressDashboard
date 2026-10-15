"""Translation between SQLAlchemy models and domain entities.

This is the single seam where persistence rows become domain objects, keeping
the rest of the codebase free of ORM knowledge.
"""

from decimal import Decimal

from spd.domain import entities as domain
from spd.domain import readmodels
from spd.domain.enums import (
    ActivityKind,
    CursusKind,
    EnrollmentStatus,
    ProjectKind,
    Role,
)
from spd.infrastructure.db import models as orm

__all__ = [
    "to_account",
    "to_activity_event",
    "to_activity_item",
    "to_campus",
    "to_cursus",
    "to_daily_snapshot",
    "to_enrollment",
    "to_project",
    "to_skill",
    "to_skill_level",
    "to_student",
    "to_student_progress",
]


def to_account(row: orm.User) -> domain.Account:
    return domain.Account(
        id=row.id,
        login=row.login,
        role=Role(row.role),
        password_hash=row.password_hash,
    )


def to_campus(row: orm.Campus) -> domain.Campus:
    return domain.Campus(
        id=row.id,
        code=row.code,
        name=row.name,
        city=row.city,
        country=row.country,
    )


def to_cursus(row: orm.Cursus) -> domain.Cursus:
    return domain.Cursus(
        id=row.id,
        code=row.code,
        name=row.name,
        kind=CursusKind(row.kind),
    )


def to_skill(row: orm.Skill) -> domain.Skill:
    return domain.Skill(id=row.id, code=row.code, name=row.name)


def to_project(row: orm.Project) -> domain.Project:
    return domain.Project(
        id=row.id,
        slug=row.slug,
        name=row.name,
        difficulty=row.difficulty,
        estimated_hours=row.estimated_hours,
        kind=ProjectKind(row.kind),
        cursus_id=row.cursus_id,
    )


def to_student(row: orm.User) -> domain.Student:
    return domain.Student(
        id=row.id,
        login=row.login,
        email=row.email,
        full_name=row.full_name,
        role=Role(row.role),
        campus_id=row.campus_id,
        blackholed_at=row.blackholed_at,
        created_at=row.created_at,
    )


def to_enrollment(row: orm.Enrollment) -> domain.Enrollment:
    return domain.Enrollment(
        id=row.id,
        student_id=row.user_id,
        project_id=row.project_id,
        status=EnrollmentStatus(row.status),
        final_mark=row.final_mark,
        attempt=row.attempt,
        started_at=row.started_at,
        finished_at=row.finished_at,
    )


def to_skill_level(row: orm.SkillLevel) -> domain.SkillLevel:
    return domain.SkillLevel(
        student_id=row.user_id,
        skill_id=row.skill_id,
        level=row.level,
        updated_at=row.updated_at,
    )


def to_activity_event(row: orm.ActivityEvent) -> domain.ActivityEvent:
    return domain.ActivityEvent(
        id=row.id,
        student_id=row.user_id,
        kind=ActivityKind(row.kind),
        day=row.day,
        xp_delta=row.xp_delta,
        project_id=row.project_id,
        occurred_at=row.occurred_at,
        payload=dict(row.payload),
    )


def to_daily_snapshot(row: orm.DailySnapshot) -> domain.DailySnapshot:
    return domain.DailySnapshot(
        student_id=row.user_id,
        day=row.day,
        xp_total=row.xp_total,
        level=row.level,
        projects_done=row.projects_done,
    )


def to_activity_item(
    row: orm.ActivityEvent, *, login: str, project_slug: str | None
) -> readmodels.ActivityItem:
    return readmodels.ActivityItem(
        id=row.id,
        student_id=row.user_id,
        student_login=login,
        kind=ActivityKind(row.kind),
        day=row.day,
        xp_delta=row.xp_delta,
        project_slug=project_slug,
        occurred_at=row.occurred_at,
        payload=dict(row.payload),
    )


def to_student_progress(
    row: orm.User,
    *,
    campus: orm.Campus,
    xp_total: int,
    level: Decimal,
    projects_done: int,
) -> readmodels.StudentProgress:
    return readmodels.StudentProgress(
        student=to_student(row),
        campus=to_campus(campus),
        xp_total=int(xp_total),
        level=Decimal(level),
        projects_done=int(projects_done),
    )
