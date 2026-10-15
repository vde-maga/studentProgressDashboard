"""Migration-level integration tests against a real PostgreSQL."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.integration

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


def _url(alembic_config: Config) -> str:
    url = alembic_config.get_main_option("sqlalchemy.url")
    assert url is not None
    return url


def _table_names(url: str) -> set[str]:
    engine = create_engine(url)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_migrations_produce_the_expected_schema(alembic_config: Config) -> None:
    assert _table_names(_url(alembic_config)) >= EXPECTED_TABLES


def test_no_pending_migration_drift(alembic_config: Config) -> None:
    # Raises when autogenerate would emit any operation: models == migrations.
    command.check(alembic_config)


def test_downgrade_and_upgrade_round_trip(alembic_config: Config) -> None:
    url = _url(alembic_config)

    command.downgrade(alembic_config, "base")
    remaining = _table_names(url) - {"alembic_version"}
    assert remaining == set()

    command.upgrade(alembic_config, "head")
    assert _table_names(url) >= EXPECTED_TABLES
