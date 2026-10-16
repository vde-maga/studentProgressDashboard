# Architecture

A deliberately small, layered full-stack app. The backend owns all data and
business rules; the frontend is a pure client of a typed HTTP + SSE API.

## Backend

A classic ports-and-adapters layout, with dependencies pointing **inwards**:
`api → application → domain`, and `infrastructure` implementing the domain's
repository protocols.

```
backend/src/spd/
├── domain/          # pure: entities, enums, progress maths, repository Protocols
├── application/     # use cases: analytics queries, SSE streaming
├── infrastructure/  # SQLAlchemy models, mappers, repositories, Alembic, seeder
├── api/             # FastAPI routers, Pydantic schemas, dependencies
├── core/            # settings, logging, errors (RFC 7807), security, middleware
└── main.py          # app factory
```

- **Domain** — dataclasses and enums with no framework imports; the XP→level
  curve lives here and is unit-tested in isolation.
- **Application** — thin services that orchestrate repositories and shape read
  models. No SQL.
- **Infrastructure** — SQLAlchemy 2.0 (`AsyncSession`), repositories, explicit
  mappers between ORM rows and domain entities, and the deterministic seeder.
- **API** — FastAPI routers, request/response schemas, and `Depends`-based auth.
  Errors are emitted as problem+json.

Every phase added an ADR; see the index at the bottom.

## Frontend

```
frontend/src/
├── app/        # providers, router, AppShell
├── features/   # auth, dashboard, leaderboard, profile, activity, notfound
└── shared/     # api client, auth session, charts, ui primitives, styles, format
```

Feature code depends on `shared/`, never the other way around. The API client
handles the bearer token and transparent single-flight refresh; TanStack Query
owns caching; TanStack Router owns navigation (code-based routes). Charts are
hand-built SVG over a pure geometry module.

## Request lifecycle

```mermaid
sequenceDiagram
    participant B as Browser
    participant V as Vite (dev proxy)
    participant A as FastAPI
    participant D as PostgreSQL

    B->>V: POST /api/v1/auth/login
    V->>A: (proxied)
    A->>D: SELECT user; verify Argon2id
    A-->>B: access (15m) + refresh (14d)
    B->>V: GET /api/v1/students/{login} (Bearer)
    V->>A: (proxied)
    A->>A: verify JWT, check owner-or-staff
    A->>D: aggregate read
    A-->>B: JSON
    Note over B,A: on 401, the client refreshes once and retries
```

## Live activity (SSE)

`GET /api/v1/events/stream` is a **cursor** over `activity_events`, not a
broadcast of state. The server records the current head id on connect, then
polls for newer rows, emitting each as an SSE frame with its `id:`; the browser
reconnects automatically with `Last-Event-ID` and resumes exactly where it left
off. Periodic heartbeats keep intermediaries from closing the connection. See
[ADR 0003](adr/0003-analytics-and-sse.md).

Because `EventSource` cannot set headers, the access token rides in the `token`
query parameter.

## Testing

A three-layer pyramid, mirrored in CI:

| Layer       | Tooling                 | Scope                                          |
| ----------- | ----------------------- | ---------------------------------------------- |
| Unit        | pytest / vitest         | domain maths, mappers, hooks, components       |
| Integration | pytest + testcontainers | repositories, API routes, auth, SSE against PG |
| End-to-end  | Playwright (real stack) | sign-in, dashboard, live SSE, authorization    |

See [ADR 0006](adr/0006-end-to-end-tests.md) for the E2E design.

## Reproducibility

`flake.nix` pins the whole toolchain (Python 3.13, Node 24, PostgreSQL 17,
Playwright browsers, ruff/mypy/prettier) so every machine and CI run uses
identical versions. `nix fmt` and `nix flake check` are the same formatters and
checks CI runs.

## ADR index

- [0001 — Data layer](adr/0001-data-layer.md)
- [0002 — Authentication](adr/0002-authentication.md)
- [0003 — Analytics and SSE](adr/0003-analytics-and-sse.md)
- [0004 — Frontend foundation](adr/0004-frontend-foundation.md)
- [0005 — Profile, charts and live feed](adr/0005-profile-charts-and-live-feed.md)
- [0006 — End-to-end tests](adr/0006-end-to-end-tests.md)
- [0007 — Scope: a portfolio demo](adr/0007-scope-and-deployment.md)
