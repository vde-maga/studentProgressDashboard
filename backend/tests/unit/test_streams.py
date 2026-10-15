"""Tests for the framework-free SSE activity stream generator."""

from datetime import UTC, date, datetime

from spd.application.streams import FetchEvents, Heartbeat, stream_activity
from spd.domain.enums import ActivityKind
from spd.domain.readmodels import ActivityItem


def _item(identifier: int) -> ActivityItem:
    return ActivityItem(
        id=identifier,
        student_id=1,
        student_login="alice",
        kind=ActivityKind.COMMIT,
        day=date(2026, 1, 1),
        xp_delta=10,
        project_slug="libft",
        occurred_at=datetime(2026, 1, 1, 9, tzinfo=UTC),
        payload={},
    )


def _fetch_releasing(items: list[ActivityItem]) -> tuple[list[int], FetchEvents]:
    seen: list[int] = []

    async def fetch(last_id: int) -> list[ActivityItem]:
        seen.append(last_id)
        return [item for item in items if item.id > last_id]

    return seen, fetch


async def test_events_are_yielded_in_order() -> None:
    _, fetch = _fetch_releasing([_item(1), _item(2)])

    produced = [
        item
        async for item in stream_activity(
            fetch, last_id=0, poll_interval=0, heartbeat_interval=999, max_polls=1
        )
    ]

    assert [item.id for item in produced] == [1, 2]  # type: ignore[union-attr]


async def test_the_cursor_advances_between_polls() -> None:
    seen, fetch = _fetch_releasing([_item(1), _item(2)])

    _ = [
        item
        async for item in stream_activity(
            fetch, last_id=0, poll_interval=0, heartbeat_interval=999, max_polls=2
        )
    ]

    assert seen == [0, 2]


async def test_heartbeat_is_emitted_when_idle() -> None:
    _, fetch = _fetch_releasing([])

    produced = [
        item
        async for item in stream_activity(
            fetch, last_id=0, poll_interval=1, heartbeat_interval=1, max_polls=1
        )
    ]

    assert produced == [Heartbeat()]
