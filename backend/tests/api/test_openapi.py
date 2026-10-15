"""Tests for OpenAPI metadata and the docs toggle."""

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from spd import __version__
from spd.core.config import Settings
from spd.main import create_app


async def test_openapi_carries_metadata(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()

    assert schema["info"]["title"] == "Student Progress Dashboard API"
    assert schema["info"]["version"] == __version__
    assert schema["info"]["description"]


async def test_health_is_tagged_for_grouping(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()

    operation = schema["paths"]["/api/v1/health"]["get"]
    assert operation["tags"] == ["health"]
    assert operation["summary"] == "Liveness probe"


async def test_interactive_docs_available_by_default(client: AsyncClient) -> None:
    assert (await client.get("/docs")).status_code == 200


async def test_docs_can_be_disabled(settings: Settings) -> None:
    app: FastAPI = create_app(settings.model_copy(update={"docs_enabled": False}))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        for path in ("/docs", "/redoc", "/openapi.json"):
            response = await http.get(path)
            assert response.status_code == 404, path
