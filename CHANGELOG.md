# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Frontend error boundary with a dedicated error page, a notification toaster
  and a retry policy that ignores deterministic `4xx` responses
  ([ADR 0008](docs/adr/0008-error-handling-and-stream-lifecycle.md)).
- Accessibility pass: a skip link, focus moved to `<main>` on navigation,
  live-region status for the live stream, and an automated a11y E2E check.
- Frontend coverage gate (v8) with the lcov report uploaded as a CI artifact,
  plus tests for the login page, leaderboard, auth provider, token storage, API
  wrappers and shared UI primitives.
- Non-blocking dependency-audit CI job (`pip-audit`, `pnpm audit`) and a
  Dependabot configuration for `uv`, npm, GitHub Actions and Nix inputs.
- Contributor, security and changelog documentation.

### Changed

- The SSE stream is now bounded in time and closes cleanly on a mid-stream
  database failure, resuming from `Last-Event-ID`
  ([ADR 0008](docs/adr/0008-error-handling-and-stream-lifecycle.md)).

## [1.0.0] — 2026-10-16

Full-stack student progress dashboard: FastAPI + PostgreSQL backend and a
React 19 + TypeScript SPA, reproducible in one Nix dev shell.

### Added

- Data layer with a pure domain, SQLAlchemy 2.0 repositories, Alembic
  migrations and a deterministic seeder ([ADR 0001](docs/adr/0001-data-layer.md)).
- JWT authentication with Argon2id hashing, stateless access/refresh tokens and
  owner-or-staff authorization ([ADR 0002](docs/adr/0002-authentication.md)).
- Analytics API — students, progress, activity, skills, leaderboard, cohort
  summary — with a cursor-based SSE live feed
  ([ADR 0003](docs/adr/0003-analytics-and-sse.md)).
- React SPA foundation (Vite, TanStack Router/Query, design tokens)
  ([ADR 0004](docs/adr/0004-frontend-foundation.md)), the student profile with
  hand-built SVG charts and the live feed
  ([ADR 0005](docs/adr/0005-profile-charts-and-live-feed.md)).
- Playwright end-to-end suite against the real stack
  ([ADR 0006](docs/adr/0006-end-to-end-tests.md)).
- CI pipeline (lint, test, integration, Nix, frontend, E2E) and the
  architecture guide.

## [0.4.0] — 2026-10-16

### Added

- Frontend dashboard: application shell, cohort dashboard, leaderboard,
  student profile, sign-in flow and Playwright end-to-end tests.

## [0.3.0] — 2026-10-16

### Added

- CI pipeline gating every change (lint, tests, integration, Nix, frontend,
  end-to-end).

## [0.2.0] — 2026-10-16

### Added

- JWT authentication and the analytics API with the SSE stream.

## [0.1.0] — 2026-10-15

### Added

- Backend foundation: project skeleton, PostgreSQL data layer and the
  deterministic seeder.

[Unreleased]: https://github.com/vde-maga/studentProgressDashboard/compare/v1.0.0...dev
[1.0.0]: https://github.com/vde-maga/studentProgressDashboard/releases/tag/v1.0.0
[0.4.0]: https://github.com/vde-maga/studentProgressDashboard/releases/tag/v0.4.0
[0.3.0]: https://github.com/vde-maga/studentProgressDashboard/releases/tag/v0.3.0
[0.2.0]: https://github.com/vde-maga/studentProgressDashboard/releases/tag/v0.2.0
[0.1.0]: https://github.com/vde-maga/studentProgressDashboard/releases/tag/v0.1.0
