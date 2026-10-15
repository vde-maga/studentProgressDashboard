"""Schema-shape tests that run without a database."""

import pytest
from sqlalchemy import BigInteger
from sqlalchemy.schema import Constraint, PrimaryKeyConstraint

from spd.infrastructure.db import models
from spd.infrastructure.db.base import Base

EXPECTED_TABLES = {
    "activity_events",
    "audits",
    "campuses",
    "cursus",
    "daily_snapshots",
    "enrollments",
    "projects",
    "skill_levels",
    "skills",
    "users",
}


def test_every_model_is_registered() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_primary_keys_follow_naming_convention() -> None:
    for table in Base.metadata.tables.values():
        pk = next(
            constraint
            for constraint in table.constraints
            if isinstance(constraint, PrimaryKeyConstraint)
        )
        assert pk.name == f"pk_{table.name}"


def test_unique_and_foreign_keys_are_named() -> None:
    users = Base.metadata.tables["users"]
    constraint_names = {
        constraint.name
        for constraint in users.constraints
        if isinstance(constraint, Constraint)
    }
    assert "uq_users_login" in constraint_names
    assert "uq_users_email" in constraint_names

    fk_names = {
        fk.constraint.name
        for fk in users.foreign_keys
        if fk.constraint is not None
    }
    assert fk_names == {"fk_users_campus_id_campuses"}


def test_surrogate_keys_are_bigint_identity() -> None:
    for name in EXPECTED_TABLES - {"skill_levels", "daily_snapshots"}:
        column = Base.metadata.tables[name].c["id"]
        assert isinstance(column.type, BigInteger), name
        assert column.primary_key


@pytest.mark.parametrize(
    ("table", "constraint"),
    [
        ("users", "ck_users_role"),
        ("cursus", "ck_cursus_cursus_kind"),
        ("projects", "ck_projects_project_kind"),
        ("enrollments", "ck_enrollments_enrollment_status"),
        ("activity_events", "ck_activity_events_activity_kind"),
    ],
)
def test_enums_use_portable_check_constraints(table: str, constraint: str) -> None:
    names = {c.name for c in Base.metadata.tables[table].constraints}
    assert constraint in names


def test_check_constraints_are_named() -> None:
    enrollments = {c.name for c in Base.metadata.tables["enrollments"].constraints}
    assert {
        "ck_enrollments_attempt_positive",
        "ck_enrollments_final_mark_range",
    } <= enrollments


def test_time_series_are_indexed() -> None:
    events = Base.metadata.tables["activity_events"]
    assert "ix_activity_events_user_id_day" in {i.name for i in events.indexes}
    assert "ix_activity_events_day" in {i.name for i in events.indexes}


def test_models_module_exposes_tables() -> None:
    assert models.User.__tablename__ == "users"
