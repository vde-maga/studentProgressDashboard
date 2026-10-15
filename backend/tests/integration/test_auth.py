"""End-to-end auth flow against a real, seeded PostgreSQL."""

from collections.abc import AsyncIterator
from datetime import date

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spd.infrastructure.db import models as orm
from spd.infrastructure.db.session import get_session
from spd.infrastructure.seed import DEMO_PASSWORD, SeedConfig, Seeder

pytestmark = pytest.mark.integration

_SEED = SeedConfig(
    seed=3, student_count=4, days=20, end_date=date(2026, 10, 15), reset=True
)


@pytest.fixture(autouse=True)
async def _seeded_database(app: FastAPI, session: AsyncSession) -> None:
    await Seeder(_SEED).run(session)

    async def _provide() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _provide


async def _first_login(session: AsyncSession) -> str:
    login = await session.scalar(select(orm.User.login).order_by(orm.User.id))
    assert login is not None
    return login


async def test_seeded_user_can_log_in_and_fetch_profile(
    client: AsyncClient, session: AsyncSession
) -> None:
    login = await _first_login(session)

    response = await client.post(
        "/api/v1/auth/login", json={"login": login, "password": DEMO_PASSWORD}
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    profile = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert profile.status_code == 200
    assert profile.json()["login"] == login


async def test_wrong_demo_password_is_rejected(
    client: AsyncClient, session: AsyncSession
) -> None:
    login = await _first_login(session)

    response = await client.post(
        "/api/v1/auth/login", json={"login": login, "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


async def test_refresh_rotates_the_token_pair(
    client: AsyncClient, session: AsyncSession
) -> None:
    login = await _first_login(session)
    tokens = (
        await client.post(
            "/api/v1/auth/login", json={"login": login, "password": DEMO_PASSWORD}
        )
    ).json()

    refreshed = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]
