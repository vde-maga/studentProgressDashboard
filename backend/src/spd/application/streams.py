"""Server-sent-events streaming logic, independent of the web framework.

The campaign feed is a cursor over activity events: each poll asks for events
after the last id already delivered, so the client never misses or re-receives
a row. Heartbeats keep idle connections alive. Keeping this a plain async
generator lets it be tested without a running server or a database.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass

from spd.domain.readmodels import ActivityItem

__all__ = ["Heartbeat", "stream_activity"]

FetchEvents = Callable[[int], Awaitable[list[ActivityItem]]]


@dataclass(frozen=True, slots=True)
class Heartbeat:
    """Sentinel emitted when a poll yields no new events."""


async def stream_activity(
    fetch: FetchEvents,
    *,
    last_id: int,
    poll_interval: float,
    heartbeat_interval: float,
    max_polls: int | None = None,
    max_duration: float | None = None,
) -> AsyncIterator[ActivityItem | Heartbeat]:
    """Poll ``fetch`` for events newer than ``last_id`` and yield them.

    Yields each :class:`ActivityItem` in arrival order, and a
    :class:`Heartbeat` once ``heartbeat_interval`` seconds pass without new
    events. ``max_polls`` bounds the loop (used by tests) and ``max_duration``
    bounds how long the stream may live, after which the generator ends and the
    client reconnects from ``Last-Event-ID``.
    """
    since = last_id
    quiet_for = 0.0
    polls = 0
    deadline = None if max_duration is None else time.monotonic() + max_duration
    while (max_polls is None or polls < max_polls) and (
        deadline is None or time.monotonic() < deadline
    ):
        events = await fetch(since)
        if events:
            quiet_for = 0.0
            for event in events:
                since = event.id
                yield event
        else:
            quiet_for += poll_interval
            if quiet_for >= heartbeat_interval:
                quiet_for = 0.0
                yield Heartbeat()
        polls += 1
        await asyncio.sleep(poll_interval)
