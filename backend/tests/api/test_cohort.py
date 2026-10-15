"""Unit tests for the cohort summary endpoint, with fakes."""

import pytest
from httpx import AsyncClient

from spd.core.config import Settings
from spd.core.security import create_access_token
from spd.domain.enums import Role

pytestmark = pytest.mark.usefixtures("use_fake_analytics")


async def test_cohort_summary_is_returned(
    client: AsyncClient, settings: Settings
) -> None:
    token = create_access_token(
        subject=1, login="alice", role=Role.STUDENT, settings=settings
    )

    response = await client.get(
        "/api/v1/cohort/summary", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "student_count": 2,
        "total_xp": 500,
        "average_level": "1.50",
        "projects_done": 4,
        "active_last_7_days": 2,
    }


async def test_cohort_summary_requires_a_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/cohort/summary")

    assert response.status_code == 401
