"""End-to-end analytics API tests against a real, seeded PostgreSQL."""

import asyncio
from collections.abc import AsyncIterator
from datetime import date

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from spd.core.config import Environment, Settings
from spd.core.security import create_access_token
from spd.domain.enums import Role
from spd.infrastructure.db import models as orm
from spd.infrastructure.db.session import create_session_factory, get_session
from spd.infrastructure.seed import DEMO_PASSWORD, SeedConfig, Seeder
from spd.main import create_app

pytestmark = pytest.mark.integration

_SEED = SeedConfig(seed=5, student_count=6, days=45, end_date=date(2026, 10, 15))


@pytest.fixture(autouse=True)
async def _seeded_database(app: FastAPI, session: AsyncSession) -> AsyncIterator[None]:
    await Seeder(_SEED).run(session)

    async def _provide() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _provide
    yield
    app.dependency_overrides.clear()


async def _logins(session: AsyncSession) -> list[str]:
    rows = await session.scalars(select(orm.User.login).order_by(orm.User.id))
    return list(rows)


async def _token(client: AsyncClient, login: str) -> str:
    response = await client.post(
        "/api/v1/auth/login", json={"login": login, "password": DEMO_PASSWORD}
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


async def test_student_reads_own_profile_and_is_denied_another(
    client: AsyncClient, session: AsyncSession
) -> None:
    first, second = (await _logins(session))[:2]
    token = await _token(client, first)
    headers = {"Authorization": f"Bearer {token}"}

    own = await client.get(f"/api/v1/students/{first}", headers=headers)
    assert own.status_code == 200
    assert own.json()["login"] == first

    other = await client.get(f"/api/v1/students/{second}", headers=headers)
    assert other.status_code == 403


async def test_leaderboard_is_ranked(
    client: AsyncClient, session: AsyncSession
) -> None:
    first = (await _logins(session))[0]
    headers = {"Authorization": f"Bearer {await _token(client, first)}"}

    response = await client.get("/api/v1/leaderboard", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body[0]["rank"] == 1
    xps = [row["xp_total"] for row in body]
    assert xps == sorted(xps, reverse=True)


async def test_cohort_summary_is_consistent(
    client: AsyncClient, session: AsyncSession
) -> None:
    first = (await _logins(session))[0]
    headers = {"Authorization": f"Bearer {await _token(client, first)}"}

    response = await client.get("/api/v1/cohort/summary", headers=headers)

    assert response.status_code == 200
    assert response.json()["student_count"] == _SEED.student_count


async def test_student_progress_activity_and_skills(
    client: AsyncClient, session: AsyncSession
) -> None:
    first = (await _logins(session))[0]
    headers = {"Authorization": f"Bearer {await _token(client, first)}"}

    progress = await client.get(f"/api/v1/students/{first}/progress", headers=headers)
    activity = await client.get(f"/api/v1/students/{first}/activity", headers=headers)
    skills = await client.get(f"/api/v1/students/{first}/skills", headers=headers)

    assert progress.status_code == 200 and progress.json()
    assert activity.status_code == 200 and activity.json()
    assert skills.status_code == 200 and skills.json()


async def test_event_stream_heartbeats(engine: AsyncEngine) -> None:
    """The stream opens and keeps the connection alive with heartbeats.

    ``httpx.ASGITransport`` buffers a response until the ASGI app returns, so it
    cannot observe an infinite SSE stream. We instead drive the app at the ASGI
    layer and disconnect once the first heartbeat arrives, exercising the real
    firewall (routing, auth, database) and framing.
    """
    settings = Settings(
        _env_file=None,
        environment=Environment.TESTING,
        sse_poll_interval_seconds=0.01,
        sse_heartbeat_seconds=0.01,
    )
    app = create_app(settings)
    app.state.session_factory = create_session_factory(engine)
    token = create_access_token(
        subject=1, login="alice", role=Role.STUDENT, settings=settings
    )

    status, frames = await _drive_stream(app, token=token, stop_after=b": heartbeat")

    assert status == 200
    assert frames[0] == b": connected\n\n"
    assert any(b": heartbeat" in frame for frame in frames)


async def _drive_stream(
    app: object, *, token: str, stop_after: bytes
) -> tuple[int, list[bytes]]:
    """Run the SSE endpoint at the ASGI layer, disconnecting after a frame."""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/v1/events/stream",
        "raw_path": b"/api/v1/events/stream",
        "query_string": f"token={token}".encode(),
        "root_path": "",
        "headers": [(b"host", b"test")],
        "server": ("test", 80),
        "client": ("127.0.0.1", 12345),
    }
    status = 0
    frames: list[bytes] = []
    stop = asyncio.Event()

    async def receive() -> dict[str, object]:
        await stop.wait()
        return {"type": "http.disconnect"}

    async def send(message: dict[str, object]) -> None:
        nonlocal status
        if message["type"] == "http.response.start":
            status = int(message["status"])  # type: ignore[call-overload]
        elif message["type"] == "http.response.body":
            body = message.get("body", b"")
            if isinstance(body, bytes) and body:
                frames.append(body)
                if stop_after in body:
                    stop.set()

    await app(scope, receive, send)  # type: ignore[operator]
    return status, frames
