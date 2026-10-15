"""Unit tests for the student analytics endpoints, with fakes."""

import pytest
from httpx import AsyncClient

from spd.core.config import Settings
from spd.core.security import create_access_token
from spd.domain.enums import Role

pytestmark = pytest.mark.usefixtures("use_fake_analytics")


def _auth(login: str, role: Role, settings: Settings) -> dict[str, str]:
    token = create_access_token(subject=1, login=login, role=role, settings=settings)
    return {"Authorization": f"Bearer {token}"}


async def test_profile_owner_can_read_themselves(
    client: AsyncClient, settings: Settings
) -> None:
    response = await client.get(
        "/api/v1/students/alice", headers=_auth("alice", Role.STUDENT, settings)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["login"] == "alice"
    assert body["xp_total"] == 400
    assert body["rank"] == 1
    assert body["campus"]["code"] == "LIS"
    assert body["current_streak"] == 3


async def test_profile_hides_another_students_data(
    client: AsyncClient, settings: Settings
) -> None:
    response = await client.get(
        "/api/v1/students/bob", headers=_auth("alice", Role.STUDENT, settings)
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


async def test_profile_staff_can_read_anyone(
    client: AsyncClient, settings: Settings
) -> None:
    response = await client.get(
        "/api/v1/students/bob", headers=_auth("root", Role.STAFF, settings)
    )

    assert response.status_code == 200
    assert response.json()["login"] == "bob"


async def test_profile_requires_a_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/students/alice")

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


async def test_profile_unknown_student_is_not_found(
    client: AsyncClient, settings: Settings
) -> None:
    response = await client.get(
        "/api/v1/students/ghost", headers=_auth("root", Role.ADMIN, settings)
    )

    assert response.status_code == 404
    assert response.json()["code"] == "student_not_found"


async def test_roster_requires_a_staff_role(
    client: AsyncClient, settings: Settings
) -> None:
    denied = await client.get(
        "/api/v1/students", headers=_auth("alice", Role.STUDENT, settings)
    )
    allowed = await client.get(
        "/api/v1/students", headers=_auth("root", Role.ADMIN, settings)
    )

    assert denied.status_code == 403
    assert allowed.status_code == 200
    body = allowed.json()
    assert body["total"] == 2
    assert [item["login"] for item in body["items"]] == ["alice", "bob"]


async def test_progress_endpoint_returns_the_series(
    client: AsyncClient, settings: Settings
) -> None:
    response = await client.get(
        "/api/v1/students/alice/progress",
        headers=_auth("alice", Role.STUDENT, settings),
        params={"since": "2026-01-02"},
    )

    assert response.status_code == 200
    assert [point["day"] for point in response.json()] == ["2026-01-02", "2026-01-03"]


async def test_activity_endpoint_returns_the_feed(
    client: AsyncClient, settings: Settings
) -> None:
    response = await client.get(
        "/api/v1/students/alice/activity",
        headers=_auth("alice", Role.STUDENT, settings),
        params={"limit": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["kind"] == "project_validated"
    assert body[0]["project_slug"] == "push_swap"


async def test_skills_endpoint_returns_levels(
    client: AsyncClient, settings: Settings
) -> None:
    response = await client.get(
        "/api/v1/students/alice/skills",
        headers=_auth("alice", Role.STUDENT, settings),
    )

    assert response.status_code == 200
    assert response.json() == [{"code": "c", "name": "C", "level": "3.50"}]


async def test_analytics_endpoints_are_documented(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()
    paths = schema["paths"]

    for path in (
        "/api/v1/students",
        "/api/v1/students/{login}",
        "/api/v1/students/{login}/progress",
        "/api/v1/students/{login}/activity",
        "/api/v1/students/{login}/skills",
        "/api/v1/leaderboard",
        "/api/v1/cohort/summary",
        "/api/v1/events/stream",
    ):
        assert path in paths, path

    assert paths["/api/v1/students"]["get"]["tags"] == ["students"]
