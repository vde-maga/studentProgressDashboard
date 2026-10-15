"""Tests for the database-backed readiness probe."""

from collections.abc import AsyncIterator, Callable

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.exc import OperationalError

from spd.infrastructure.db.session import get_session


class _OkSession:
    """Fake session whose ``execute`` always succeeds."""

    async def execute(self, *args: object, **kwargs: object) -> None:
        return None


class _DownSession:
    """Fake session whose ``execute`` raises a database error."""

    async def execute(self, *args: object, **kwargs: object) -> None:
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))


def _override(session: object) -> Callable[[], AsyncIterator[object]]:
    async def _dependency() -> AsyncIterator[object]:
        yield session

    return _dependency


async def test_readiness_ok(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_session] = _override(_OkSession())

    response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "up"}


async def test_readiness_degrades_to_problem_json(
    app: FastAPI, client: AsyncClient
) -> None:
    app.dependency_overrides[get_session] = _override(_DownSession())

    response = await client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "database_unavailable"


async def test_readiness_documented_in_openapi(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()

    assert "/api/v1/health/ready" in schema["paths"]
