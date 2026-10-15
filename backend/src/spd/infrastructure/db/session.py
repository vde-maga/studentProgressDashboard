"""Async engine, session factory and the FastAPI session dependency."""

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from spd.core.config import Settings

__all__ = [
    "SessionFactory",
    "create_engine",
    "create_session_factory",
    "get_session",
    "get_session_factory",
]

SessionFactory = async_sessionmaker[AsyncSession]


def create_engine(settings: Settings) -> AsyncEngine:
    """Build an async engine from settings (no connection is opened yet)."""
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
    )


def create_session_factory(engine: AsyncEngine) -> SessionFactory:
    """Build a session factory that keeps objects usable after commit."""
    return async_sessionmaker(engine, expire_on_commit=False)


def get_session_factory(request: Request) -> SessionFactory | None:
    """Return the app's session factory, if the lifespan configured one."""
    factory = getattr(request.app.state, "session_factory", None)
    assert factory is None or isinstance(factory, async_sessionmaker)
    return factory


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped session.

    The factory is created once by the application lifespan and stored on
    ``app.state``; tests override this dependency to point at an ephemeral
    database.
    """
    factory = get_session_factory(request)
    if factory is None:
        raise RuntimeError("database session factory is not configured")
    async with factory() as session:
        yield session
