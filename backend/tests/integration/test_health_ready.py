"""End-to-end readiness probe against the container database."""

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from spd.infrastructure.db.session import get_session

pytestmark = pytest.mark.integration


async def test_readiness_reports_ready_with_a_real_database(
    app: FastAPI, client: AsyncClient, session: AsyncSession
) -> None:
    async def _provide() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _provide

    response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "up"}
