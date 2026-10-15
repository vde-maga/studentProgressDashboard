"""Shared pytest fixtures."""

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from spd.core.config import Environment, Settings
from spd.main import create_app


@pytest.fixture
def settings() -> Settings:
    """Deterministic settings that never read the developer's `.env`."""
    return Settings(_env_file=None, environment=Environment.TESTING)


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http
