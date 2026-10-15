"""Static conformance: the SQL implementations must satisfy the domain ports.

Assigning each class to a ``type[Protocol]`` variable makes mypy verify — at
type-check time, not runtime — that a concrete repository honours the
interface the domain depends on.
"""

from spd.domain.repositories import AnalyticsRepository, StudentRepository
from spd.infrastructure.repositories import (
    SqlAnalyticsRepository,
    SqlStudentRepository,
)


def test_sql_repositories_satisfy_domain_protocols() -> None:
    student_repository: type[StudentRepository] = SqlStudentRepository
    analytics_repository: type[AnalyticsRepository] = SqlAnalyticsRepository

    assert student_repository is SqlStudentRepository
    assert analytics_repository is SqlAnalyticsRepository
