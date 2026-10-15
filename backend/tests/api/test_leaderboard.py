"""Unit tests for the leaderboard endpoint, with fakes."""

import pytest
from httpx import AsyncClient

from spd.core.config import Settings
from spd.core.security import create_access_token
from spd.domain.enums import Role

pytestmark = pytest.mark.usefixtures("use_fake_analytics")


def _auth(settings: Settings) -> dict[str, str]:
    token = create_access_token(
        subject=1, login="alice", role=Role.STUDENT, settings=settings
    )
    return {"Authorization": f"Bearer {token}"}


async def test_leaderboard_is_ranked_and_paginated(
    client: AsyncClient, settings: Settings
) -> None:
    response = await client.get(
        "/api/v1/leaderboard",
        headers=_auth(settings),
        params={"limit": 1, "offset": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["login"] == "bob"
    assert body[0]["rank"] == 2
    assert body[0]["campus_code"] == "LIS"


async def test_leaderboard_requires_a_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/leaderboard")

    assert response.status_code == 401
