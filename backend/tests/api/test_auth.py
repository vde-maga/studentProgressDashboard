"""Unit tests for the auth endpoints, with in-memory repositories."""

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from httpx import AsyncClient

from spd.api.deps import (
    Principal,
    get_account_repository,
    get_student_repository,
    require_roles,
)
from spd.core.config import Settings
from spd.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
)
from spd.domain.entities import Account, Student
from spd.domain.enums import Role

PASSWORD = "s3cret-password"


class _FakeAccountRepository:
    def __init__(self, accounts: list[Account]) -> None:
        self._accounts = {account.login: account for account in accounts}

    async def find_by_login(self, login: str) -> Account | None:
        return self._accounts.get(login)


class _FakeStudentRepository:
    def __init__(self, students: list[Student]) -> None:
        self._students = {student.login: student for student in students}

    async def get_by_login(self, login: str) -> Student | None:
        return self._students.get(login)

    async def list_students(self, *, limit: int, offset: int) -> list[Student]:
        return list(self._students.values())[offset : offset + limit]

    async def count(self) -> int:
        return len(self._students)


def _account(login: str = "msilva", role: Role = Role.STUDENT) -> Account:
    return Account(id=1, login=login, role=role, password_hash=hash_password(PASSWORD))


def _student(login: str = "msilva", role: Role = Role.STUDENT) -> Student:
    return Student(
        id=1,
        login=login,
        email=f"{login}@student.42.fr",
        full_name="Maria Silva",
        role=role,
        campus_id=1,
        blackholed_at=None,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


@pytest.fixture(autouse=True)
def _fake_repositories(app: FastAPI) -> Iterator[None]:
    account = _account()
    student = _student()
    app.dependency_overrides[get_account_repository] = lambda: _FakeAccountRepository(
        [account]
    )
    app.dependency_overrides[get_student_repository] = lambda: _FakeStudentRepository(
        [student]
    )
    yield
    app.dependency_overrides.clear()


async def test_login_returns_a_token_pair(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"login": "msilva", "password": PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]
    assert body["expires_in"] == 15 * 60


async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"login": "msilva", "password": "nope"}
    )

    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["code"] == "invalid_credentials"


async def test_login_rejects_unknown_login(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"login": "ghost", "password": PASSWORD}
    )

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


async def test_login_validates_the_payload(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/login", json={"login": ""})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


async def test_me_requires_a_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["code"] == "not_authenticated"


async def test_me_rejects_a_refresh_token(
    client: AsyncClient, settings: Settings
) -> None:
    refresh = create_refresh_token(
        subject=1, login="msilva", role=Role.STUDENT, settings=settings
    )

    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh}"}
    )

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


async def test_me_returns_the_profile(client: AsyncClient, settings: Settings) -> None:
    token = create_access_token(
        subject=1, login="msilva", role=Role.STUDENT, settings=settings
    )

    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["login"] == "msilva"
    assert body["email"] == "msilva@student.42.fr"
    assert "password_hash" not in body


async def test_refresh_issues_new_tokens(
    client: AsyncClient, settings: Settings
) -> None:
    refresh = create_refresh_token(
        subject=1, login="msilva", role=Role.STUDENT, settings=settings
    )

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh}
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_refresh_rejects_an_access_token(
    client: AsyncClient, settings: Settings
) -> None:
    access = create_access_token(
        subject=1, login="msilva", role=Role.STUDENT, settings=settings
    )

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": access})

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


async def test_role_guard_allows_and_denies(
    app: FastAPI, client: AsyncClient, settings: Settings
) -> None:
    @app.get("/api/v1/admin-only")
    async def admin_only(
        _: Annotated[Principal, Depends(require_roles(Role.ADMIN))],
    ) -> dict[str, bool]:
        return {"ok": True}

    student = create_access_token(
        subject=1, login="msilva", role=Role.STUDENT, settings=settings
    )
    admin = create_access_token(
        subject=2, login="root", role=Role.ADMIN, settings=settings
    )

    denied = await client.get(
        "/api/v1/admin-only", headers={"Authorization": f"Bearer {student}"}
    )
    allowed = await client.get(
        "/api/v1/admin-only", headers={"Authorization": f"Bearer {admin}"}
    )

    assert denied.status_code == 403
    assert denied.json()["code"] == "forbidden"
    assert allowed.status_code == 200
    assert allowed.json() == {"ok": True}


def test_require_roles_needs_at_least_one_role() -> None:
    with pytest.raises(ValueError, match="at least one role"):
        require_roles()


async def test_auth_endpoints_are_documented_in_openapi(
    client: AsyncClient,
) -> None:
    schema = (await client.get("/openapi.json")).json()

    for path in ("/api/v1/auth/login", "/api/v1/auth/refresh", "/api/v1/auth/me"):
        assert path in schema["paths"], path
    assert schema["paths"]["/api/v1/auth/login"]["post"]["tags"] == ["auth"]
