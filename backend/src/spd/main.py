"""Application factory and ASGI entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from spd import __version__
from spd.api.v1.router import api_router
from spd.core.config import Settings, get_settings
from spd.core.errors import register_error_handlers
from spd.core.logging import configure_logging
from spd.core.middleware import RequestContextMiddleware
from spd.infrastructure.db.session import create_engine, create_session_factory

API_PREFIX = "/api/v1"

OPENAPI_TAGS = [
    {"name": "health", "description": "Liveness and readiness probes."},
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Own the database engine for the process lifetime.

    The engine is created lazily on startup (no connection is opened) and
    disposed on shutdown, so ``create_app`` stays side-effect free for tests.
    """
    settings: Settings = app.state.settings
    engine = create_engine(settings)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    try:
        yield
    finally:
        await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application.

    Settings may be injected (tests, alternative environments); otherwise the
    process-wide cached settings are used.
    """
    settings = settings or get_settings()
    configure_logging(settings.environment)

    docs_url = "/docs" if settings.docs_enabled else None
    app = FastAPI(
        title="Student Progress Dashboard API",
        version=__version__,
        description="Progress, activity and cohort analytics for 42 students.",
        docs_url=docs_url,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )
    app.state.settings = settings
    register_error_handlers(app)
    app.add_middleware(RequestContextMiddleware)
    # Added last so it is outermost: error responses get CORS headers too.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=API_PREFIX)
    return app


app = create_app()
