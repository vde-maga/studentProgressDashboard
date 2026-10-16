"""Server-sent-events endpoint streaming the live activity feed.

The stream is a cursor over activity events: the browser's ``EventSource`` can
reconnect and resume from ``Last-Event-ID``. Because an SSE connection can live
for a long time, each poll opens its own short-lived session instead of holding
the request session open for the connection's lifetime.
"""

import asyncio
from collections.abc import AsyncIterator
from datetime import date, datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from spd.api.deps import Principal, get_stream_principal
from spd.application.streams import Heartbeat, stream_activity
from spd.core.config import Settings
from spd.domain.enums import ActivityKind
from spd.domain.readmodels import ActivityItem
from spd.infrastructure.db.session import SessionFactory, get_session_factory
from spd.infrastructure.repositories import SqlAnalyticsRepository

router = APIRouter()

logger = structlog.get_logger("spd.events")

_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
_BATCH_SIZE = 100


class ActivityEventOut(BaseModel):
    """The SSE payload for one activity event."""

    id: int
    kind: ActivityKind
    student_login: str
    day: date
    xp_delta: int
    project_slug: str | None
    occurred_at: datetime


def _frame(item: ActivityItem) -> str:
    """Render one activity item as an SSE frame."""
    payload = ActivityEventOut(
        id=item.id,
        kind=item.kind,
        student_login=item.student_login,
        day=item.day,
        xp_delta=item.xp_delta,
        project_slug=item.project_slug,
        occurred_at=item.occurred_at,
    )
    return (
        f"id: {item.id}\n"
        f"event: {item.kind.value}\n"
        f"data: {payload.model_dump_json()}\n\n"
    )


async def _initial_last_id(factory: SessionFactory, request: Request) -> int:
    """Resume from ``Last-Event-ID`` when present, else from the current head."""
    header = request.headers.get("Last-Event-ID")
    if header is not None:
        try:
            return int(header)
        except ValueError:
            logger.info("invalid_last_event_id", value=header)
    async with factory() as session:
        return await SqlAnalyticsRepository(session).latest_event_id()


@router.get(
    "/events/stream",
    summary="Live activity stream",
    description=(
        "Stream activity events as Server-Sent Events. Authenticate by passing "
        "the access token in the `token` query parameter."
    ),
    responses={401: {"description": "Missing or invalid access token."}},
)
async def stream_events(
    request: Request,
    _: Annotated[Principal, Depends(get_stream_principal)],
) -> StreamingResponse:
    settings: Settings = request.app.state.settings
    factory = get_session_factory(request)
    if factory is None:  # pragma: no cover - lifespan always configures it
        raise RuntimeError("database session factory is not configured")
    last_id = await _initial_last_id(factory, request)

    async def fetch(since: int) -> list[ActivityItem]:
        async with factory() as session:
            repository = SqlAnalyticsRepository(session)
            return await repository.events_after(since, limit=_BATCH_SIZE)

    async def event_source() -> AsyncIterator[str]:
        yield ": connected\n\n"
        try:
            async for item in stream_activity(
                fetch,
                last_id=last_id,
                poll_interval=settings.sse_poll_interval_seconds,
                heartbeat_interval=settings.sse_heartbeat_seconds,
                max_duration=settings.sse_max_connection_seconds,
            ):
                if isinstance(item, Heartbeat):
                    yield ": heartbeat\n\n"
                else:
                    yield _frame(item)
        except asyncio.CancelledError:
            # The client went away; let the cancellation propagate.
            raise
        except Exception:
            # A transient failure (e.g. the database) must not tear the
            # connection down with a stack trace: close the response cleanly
            # and let the browser's EventSource reconnect from `Last-Event-ID`.
            logger.exception("activity_stream_failed")

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )
