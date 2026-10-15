"""Tests for the versioned health endpoint."""

from httpx import AsyncClient

from spd import __version__


async def test_health_reports_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == __version__
    assert body["environment"] == "testing"


async def test_health_documents_itself_in_openapi(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()

    assert "/api/v1/health" in schema["paths"]
    assert "get" in schema["paths"]["/api/v1/health"]
