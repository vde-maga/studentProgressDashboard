"""Application factory and ASGI entrypoint."""

from fastapi import FastAPI

from spd import __version__
from spd.api.v1.router import api_router
from spd.core.config import Settings, get_settings
from spd.core.logging import configure_logging

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application.

    Settings may be injected (tests, alternative environments); otherwise the
    process-wide cached settings are used.
    """
    settings = settings or get_settings()
    configure_logging(settings.environment)

    app = FastAPI(
        title="Student Progress Dashboard API",
        version=__version__,
        description="Progress, activity and cohort analytics for 42 students.",
    )
    app.state.settings = settings
    app.include_router(api_router, prefix=API_PREFIX)
    return app


app = create_app()
