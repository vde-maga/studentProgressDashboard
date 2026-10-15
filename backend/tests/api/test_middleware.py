"""Tests for request-id propagation, logging context and CORS."""

import structlog
from fastapi import FastAPI
from httpx import AsyncClient

REQUEST_ID_HEADER = "X-Request-ID"


async def test_request_id_is_generated_when_absent(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.headers[REQUEST_ID_HEADER]


async def test_provided_request_id_is_echoed(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/health", headers={REQUEST_ID_HEADER: "abc-123"}
    )

    assert response.headers[REQUEST_ID_HEADER] == "abc-123"


async def test_request_id_is_bound_to_logging_context(
    app: FastAPI, client: AsyncClient
) -> None:
    @app.get("/api/v1/whoami")
    async def whoami() -> dict[str, object]:
        return structlog.contextvars.get_contextvars()

    response = await client.get(
        "/api/v1/whoami", headers={REQUEST_ID_HEADER: "trace-42"}
    )

    assert response.json()["request_id"] == "trace-42"


async def test_logging_context_is_cleared_between_requests(
    client: AsyncClient,
) -> None:
    await client.get("/api/v1/health", headers={REQUEST_ID_HEADER: "first"})

    assert structlog.contextvars.get_contextvars() == {}


async def test_cors_allows_configured_origin(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/health", headers={"Origin": "http://localhost:5173"}
    )

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


async def test_cors_omits_header_for_unknown_origin(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/health", headers={"Origin": "http://evil.test"}
    )

    assert "access-control-allow-origin" not in response.headers
