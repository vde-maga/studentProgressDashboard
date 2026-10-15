"""Tests for the SSE endpoint's framing and authentication."""

from datetime import UTC, date, datetime

from httpx import AsyncClient

from spd.api.v1.events import _frame
from spd.domain.enums import ActivityKind
from spd.domain.readmodels import ActivityItem


def _item() -> ActivityItem:
    return ActivityItem(
        id=7,
        student_id=1,
        student_login="alice",
        kind=ActivityKind.COMMIT,
        day=date(2026, 1, 1),
        xp_delta=10,
        project_slug="libft",
        occurred_at=datetime(2026, 1, 1, 9, tzinfo=UTC),
        payload={},
    )


def test_frame_has_id_event_and_data_lines() -> None:
    frame = _frame(_item())

    assert frame.startswith("id: 7\n")
    assert "event: commit\n" in frame
    assert "data: " in frame
    assert '"student_login":"alice"' in frame
    assert frame.endswith("\n\n")


async def test_stream_requires_a_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/events/stream")

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


async def test_stream_rejects_an_invalid_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/events/stream", params={"token": "nope"})

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"
