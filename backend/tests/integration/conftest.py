"""Integration test fixtures backed by an ephemeral PostgreSQL container.

One container is started per test session and migrations are applied once.
Each test then runs inside a transaction that is rolled back afterwards, so
tests stay isolated without truncating tables. Requires a container engine
(docker, or rootless podman via ``DOCKER_HOST``) — deselected by default and
run with ``just test-integration``.
"""

from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.community.postgres import PostgresContainer

BACKEND_DIR = Path(__file__).resolve().parents[2]
POSTGRES_IMAGE = "postgres:17-alpine"


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    with PostgresContainer(POSTGRES_IMAGE) as postgres:
        url = postgres.get_connection_url()
        # testcontainers returns the psycopg2 scheme; we use psycopg 3 (async).
        yield url.replace("postgresql+psycopg2://", "postgresql+psycopg://")


@pytest.fixture(scope="session")
def alembic_config(postgres_url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", postgres_url)
    return config


@pytest.fixture(scope="session", autouse=True)
def _migrated(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")


@pytest_asyncio.fixture
async def engine(postgres_url: str) -> AsyncIterator[AsyncEngine]:
    created = create_async_engine(postgres_url, poolclass=NullPool)
    try:
        yield created
    finally:
        await created.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async_session = AsyncSession(
            bind=connection, join_transaction_mode="create_savepoint"
        )
        try:
            yield async_session
        finally:
            await async_session.close()
            await transaction.rollback()
