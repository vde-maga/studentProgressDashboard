"""Static conformance: the SQL implementations must satisfy the domain ports.

Assigning each class to a ``type[Protocol]`` variable makes mypy verify — at
type-check time, not runtime — that a concrete repository honours the
interface the domain depends on.
"""

from spd.domain.repositories import (
    AccountRepository,
    AnalyticsRepository,
    CampusRepository,
    CohortRepository,
    LeaderboardRepository,
    StudentRepository,
)
from spd.infrastructure.repositories import (
    SqlAccountRepository,
    SqlAnalyticsRepository,
    SqlCampusRepository,
    SqlCohortRepository,
    SqlLeaderboardRepository,
    SqlStudentRepository,
)


def test_sql_repositories_satisfy_domain_protocols() -> None:
    account_repository: type[AccountRepository] = SqlAccountRepository
    student_repository: type[StudentRepository] = SqlStudentRepository
    campus_repository: type[CampusRepository] = SqlCampusRepository
    analytics_repository: type[AnalyticsRepository] = SqlAnalyticsRepository
    leaderboard_repository: type[LeaderboardRepository] = SqlLeaderboardRepository
    cohort_repository: type[CohortRepository] = SqlCohortRepository

    assert account_repository is SqlAccountRepository
    assert student_repository is SqlStudentRepository
    assert campus_repository is SqlCampusRepository
    assert analytics_repository is SqlAnalyticsRepository
    assert leaderboard_repository is SqlLeaderboardRepository
    assert cohort_repository is SqlCohortRepository
