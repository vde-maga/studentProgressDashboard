# Student Progress Dashboard

> Full-stack dashboard for tracking student progress — Python/FastAPI + PostgreSQL backend, React 19 + TypeScript frontend, all inside a reproducible NixOS dev environment.

[![CI](https://github.com/vde-maga/studentProgressDashboard/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

## Status

The **backend is complete** (phases 1–5): PostgreSQL data layer, JWT auth and
the analytics API with a live SSE stream, behind a **CI pipeline** (phase 9).
The **React frontend** is underway: the foundation is in place (phase 6 —
routing, typed API client, auth session and design system), with the
student/leaderboard views (phase 7), end-to-end tests (phase 8) and
**final docs/release** (phase 10) still to come. The frontend runs under Vite in
development (proxied to the API); there is no production build pipeline yet.

## Quickstart (NixOS)

```bash
git clone git@github.com:vde-maga/studentProgressDashboard.git
cd studentProgressDashboard
nix develop          # or: direnv allow
just setup           # deps + git hooks
just db-up           # PostgreSQL via docker compose
just dev             # API :8000 + frontend :5173
```

## Commands

| Command                      | What it does                                     |
| ---------------------------- | ------------------------------------------------ |
| `just help`                  | List all recipes                                 |
| `just setup`                 | Install backend/frontend deps + pre-commit hooks |
| `just dev`                   | Run API + frontend in parallel                   |
| `just test`                  | pytest + vitest                                  |
| `just test-integration`      | Backend integration tests (testcontainers)       |
| `just cov`                   | Backend coverage report (gate ≥80%)              |
| `just test-frontend`         | Frontend unit tests (vitest)                     |
| `just build-frontend`        | Type-check and build the SPA (`frontend/dist`)   |
| `just test-e2e`              | Playwright end-to-end (phase 8)                  |
| `just lint`                  | ruff, mypy, tsc, eslint                          |
| `just fmt`                   | Format the whole repo (`nix fmt`)                |
| `just db-up` / `db-reset`    | Start / recreate PostgreSQL                      |
| `just migrate` / `just seed` | Alembic migrations / deterministic seed data     |
| `nix flake check`            | Nix checks (formatting, …)                       |

## Authentication

The API uses stateless JWT bearer tokens (Argon2id password hashing):

| Endpoint                    | Description                                     |
| --------------------------- | ----------------------------------------------- |
| `POST /api/v1/auth/login`   | Exchange `login` + `password` for a token pair  |
| `POST /api/v1/auth/refresh` | Exchange a refresh token for a fresh pair       |
| `GET  /api/v1/auth/me`      | Profile of the caller (requires a bearer token) |

Seeded demo accounts all share the password `42cursus!`. See
[ADR 0002](docs/adr/0002-authentication.md) for the design.

## Analytics

Read endpoints for progress data, behind the same bearer auth. Detailed views
are **owner-only**: a student reads their own data, staff/admins read anyone's.

| Endpoint                                | Who            | Returns                          |
| --------------------------------------- | -------------- | -------------------------------- |
| `GET /api/v1/students`                  | staff/admin    | Paged student roster             |
| `GET /api/v1/students/{login}`          | owner or staff | Profile, rank, level progression |
| `GET /api/v1/students/{login}/progress` | owner or staff | Daily XP/level time series       |
| `GET /api/v1/students/{login}/activity` | owner or staff | Recent activity, newest first    |
| `GET /api/v1/students/{login}/skills`   | owner or staff | Skills with current levels       |
| `GET /api/v1/leaderboard`               | authenticated  | Cohort ranked by XP              |
| `GET /api/v1/cohort/summary`            | authenticated  | Aggregate cohort statistics      |
| `GET /api/v1/events/stream`             | authenticated  | Live activity feed (SSE)         |

The stream resends nothing: it is a cursor over activity events, resumable via
`Last-Event-ID`, with periodic heartbeats. Because `EventSource` cannot set an
`Authorization` header, pass the access token as `?token=…`. See
[ADR 0003](docs/adr/0003-analytics-and-sse.md) for the design.

## Frontend

A React 19 + TypeScript SPA (Vite, TanStack Router/Query) styled with a
"ligne claire × brutalism" design system (CSS Modules over shared design
tokens). The foundation covers the sign-in flow, an authenticated session with
transparent token refresh, protected routes, and the cohort dashboard and
leaderboard views.

```bash
just dev            # API :8000 + Vite :5173 (the SPA proxies /api to the API)
just lint-frontend  # tsc --noEmit + eslint
just test-frontend  # vitest
just build-frontend # production bundle into frontend/dist
```

The dev server proxies `/api` to `http://localhost:8000`, so the browser sees a
same-origin API and no CORS is needed. Point `VITE_API_URL` at a different
origin (via `frontend/.env`) when needed. See
[ADR 0004](docs/adr/0004-frontend-foundation.md) for the design.

## Stack

- **Backend** — Python 3.13, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 17, JWT auth, SSE
- **Frontend** — React 19, TypeScript (strict), Vite, TanStack Router/Query, CSS Modules + design tokens (ligne-claire brutalist UI)
- **Quality** — pytest (+testcontainers), Hypothesis, Vitest, Playwright, ruff, mypy, coverage gate ≥80%
- **DX** — `flake.nix` (devShell, formatter, checks), `just`, `pre-commit`, `uv`, `pnpm`, GitHub Actions

## Repository layout

```
├── flake.nix        # Nix dev environment (toolchain + checks + formatter)
├── justfile         # task runner — start here with `just help`
├── compose.yaml     # PostgreSQL for local dev
├── backend/         # FastAPI app (api / application / domain / infrastructure)
├── frontend/        # React SPA (Vite + TanStack Router/Query + design tokens)
└── docs/            # ADRs (architecture notes and screenshots to come)
```

## License

See [LICENSE](LICENSE).
