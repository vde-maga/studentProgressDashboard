# Student Progress Dashboard

> Full-stack dashboard for tracking student progress — Python/FastAPI + PostgreSQL backend, React 19 + TypeScript frontend, all inside a reproducible NixOS dev environment.

[![CI](https://github.com/vde-maga/studentProgressDashboard/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

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
| `just test-e2e`              | Playwright end-to-end                            |
| `just lint`                  | ruff, mypy, tsc, eslint                          |
| `just fmt`                   | Format the whole repo (`nix fmt`)                |
| `just db-up` / `db-reset`    | Start / recreate PostgreSQL                      |
| `just migrate` / `just seed` | Alembic migrations / deterministic seed data     |
| `nix flake check`            | Nix checks (formatting, …)                       |

## Authentication

The API uses stateless JWT bearer tokens (Argon2id password hashing):

| Endpoint             | Description                                      |
| -------------------- | ------------------------------------------------ |
| `POST /api/v1/auth/login`   | Exchange `login` + `password` for a token pair |
| `POST /api/v1/auth/refresh` | Exchange a refresh token for a fresh pair      |
| `GET  /api/v1/auth/me`      | Profile of the caller (requires a bearer token)|

Seeded demo accounts all share the password `42cursus!`. See
[ADR 0002](docs/adr/0002-authentication.md) for the design.

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
├── backend/         # FastAPI app (api / core / domain / infrastructure)
├── frontend/        # React app (app / features / shared)
└── docs/            # ADRs, architecture, screenshots
```

## License

See [LICENSE](LICENSE).
