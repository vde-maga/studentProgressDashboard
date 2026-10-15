"""Fixtures for the analytics HTTP tests (fake repositories, no database)."""

from collections.abc import Iterator

import pytest
from fastapi import FastAPI

from spd.api.deps import get_analytics_service, get_student_repository
from spd.application.analytics import AnalyticsService
from tests.fakes import FakeBackend


@pytest.fixture
def backend() -> FakeBackend:
    return FakeBackend()


@pytest.fixture
def analytics_service(backend: FakeBackend) -> AnalyticsService:
    return AnalyticsService(
        students=backend.students,
        campuses=backend.campuses,
        analytics=backend.analytics,
        leaderboard=backend.leaderboard,
        cohort=backend.cohort,
    )


@pytest.fixture
def use_fake_analytics(
    app: FastAPI, backend: FakeBackend, analytics_service: AnalyticsService
) -> Iterator[None]:
    """Point the analytics endpoints at the in-memory fakes."""
    app.dependency_overrides[get_analytics_service] = lambda: analytics_service
    app.dependency_overrides[get_student_repository] = lambda: backend.students
    yield
    app.dependency_overrides.clear()
