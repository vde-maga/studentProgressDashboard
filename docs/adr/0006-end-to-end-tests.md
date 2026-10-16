# ADR 0006 — End-to-end tests with Playwright

- **Status:** Accepted
- **Date:** 2026-10-16
- **Deciders:** project author
- **Context:** Phase 8 — proving the whole thing works together, in a browser.

## Context

Unit and integration tests cover the backend and the frontend in isolation, and
each has its own fakes. Nothing yet proves the _seam_: that a real browser, the
real Vite app, the real API, JWT refresh, the SSE stream and the seeded database
work together the way a person uses them. The read-only API has no write path,
so there is also no obvious way to observe a _live_ stream event arriving while
a page is open.

## Decision

### 1. Playwright (Chromium) against the real stack

E2E tests drive a real Chromium build against the actual application: the Vite
dev server (which proxies `/api`) and a real FastAPI process backed by a real
PostgreSQL database. No request mocking, no stubbed client — the point is to
exercise the seams.

The database is deliberately **not** started by the tests: locally it is the
`docker compose` database (`just db-up`), in CI it is a GitHub Actions
`postgres:17` service. `just e2e-api` applies migrations and re-seeds the demo
data, then serves the API; Playwright's `webServer` starts both it and Vite and
reuses whatever is already running locally.

Because the seeder is deterministic (ADR 0001), the tests can rely on stable
accounts (`johnsonjoshu`, `garzaanthony`) and a known dataset without fixtures
of their own.

### 2. Drive the app the way a user does

Tests sign in through the real form, click real links and assert on
user-visible text and roles — not on CSS-module class names (which are hashed)
or internal state. The suite covers the journeys that matter:

- anonymous visitors are redirected to sign-in; bad credentials are rejected;
  sign-in then sign-out;
- the dashboard renders the cohort summary;
- a **new activity event is delivered over the live SSE stream** while the page
  is open;
- the leaderboard links to a profile, and a student may open their own profile
  but not another's (`403`).

### 2a. Simulating a live event

The API is read-only, so a page cannot trigger a new activity event by itself.
The live-stream test therefore connects, waits for the stream to be _open_ (the
UI shows its "live" marker, which means the server has fixed its cursor), then
inserts one `activity_events` row directly through `psql` and asserts the row
appears in the feed without a reload. The helper documents this deliberately.

This surfaced a latent seeder bug: bulk inserts wrote explicit ids without
advancing the identity sequences, so any later insert collided on id `1`. The
seeder now resets every sequenced table's sequence after loading.

## Consequences

- **Positive:** the tests exercise the same paths a person does — auth, the
  proxy, the SSE stream, authorization and the real seed.
- **Positive:** one browser, one worker, deterministic data: the suite runs in
  ~25 seconds.
- **Positive:** failures leave a trace and screenshot artifact in CI.
- **Negative:** E2E is the slowest, most environment-sensitive suite; it is a
  separate CI job with its own Postgres service so it never blocks the fast
  feedback of lint/unit/integration.
- **Negative:** hard-coded demo logins tie the tests to the seed; changing the
  seed means updating `e2e/support/accounts.ts`.
- **Negative:** `@playwright/test` is pinned to the exact version shipped by
  `nixpkgs` (`playwright-driver`) so the Nix-store browsers are found — bump it
  in lockstep with `flake.lock`.
