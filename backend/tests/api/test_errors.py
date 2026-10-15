"""Tests for RFC 7807 problem+json error handling."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from spd.core.config import Settings
from spd.core.errors import AppError
from spd.main import create_app

PROBLEM_JSON = "application/problem+json"


async def test_unknown_route_returns_problem_json(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"] == PROBLEM_JSON
    body = response.json()
    assert body["status"] == 404
    assert body["title"] == "Not Found"
    assert body["type"] == "about:blank"


async def test_domain_errors_map_to_problem_json(
    app: FastAPI, client: AsyncClient
) -> None:
    @app.get("/api/v1/forbidden-zone")
    async def forbidden() -> None:
        raise AppError(status_code=403, code="forbidden_zone", detail="No entry")

    response = await client.get("/api/v1/forbidden-zone")

    assert response.status_code == 403
    assert response.headers["content-type"] == PROBLEM_JSON
    body = response.json()
    assert body["code"] == "forbidden_zone"
    assert body["detail"] == "No entry"
    assert body["status"] == 403


async def test_validation_errors_are_structured(
    app: FastAPI, client: AsyncClient
) -> None:
    @app.get("/api/v1/echo")
    async def echo(n: int) -> dict[str, int]:
        return {"n": n}

    response = await client.get("/api/v1/echo", params={"n": "not-a-number"})

    assert response.status_code == 422
    assert response.headers["content-type"] == PROBLEM_JSON
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["errors"][0]["loc"] == ["query", "n"]


def test_unhandled_errors_are_masked(settings: Settings) -> None:
    app = create_app(settings)

    @app.get("/api/v1/kaboom")
    async def kaboom() -> None:
        msg = "internal secret detail"
        raise RuntimeError(msg)

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/api/v1/kaboom")

    assert response.status_code == 500
    assert response.headers["content-type"] == PROBLEM_JSON
    assert response.json()["code"] == "internal_error"
    assert "secret" not in response.text
