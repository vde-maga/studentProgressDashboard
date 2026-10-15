"""Domain enumerations.

Kept as plain ``StrEnum`` so they serialise to stable lowercase values at the
API boundary and map 1:1 to the database CHECK constraints (see ADR 0001).
"""

from enum import StrEnum

__all__ = [
    "ActivityKind",
    "CursusKind",
    "EnrollmentStatus",
    "ProjectKind",
    "Role",
]


class Role(StrEnum):
    """Authorisation role of an account."""

    STUDENT = "student"
    STAFF = "staff"
    ADMIN = "admin"


class CursusKind(StrEnum):
    """Whether a cursus is the selection piscine or the main curriculum."""

    PISCINE = "piscine"
    CURSUS = "cursus"


class ProjectKind(StrEnum):
    """Nature of a project within a cursus."""

    INNER = "inner"
    OUTER = "outer"
    EXAM = "exam"
    RUSH = "rush"


class EnrollmentStatus(StrEnum):
    """Lifecycle of a student's attempt at a project."""

    LOCKED = "locked"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_CORRECTION = "waiting_for_correction"
    FINISHED = "finished"
    FAILED = "failed"


class ActivityKind(StrEnum):
    """Source event types that feed the activity timeline."""

    LOGIN = "login"
    COMMIT = "commit"
    EVALUATION_GIVEN = "evaluation_given"
    EVALUATION_RECEIVED = "evaluation_received"
    PROJECT_VALIDATED = "project_validated"
