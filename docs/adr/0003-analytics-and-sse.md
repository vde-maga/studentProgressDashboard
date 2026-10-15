# ADR 0003 — Analytics endpoints, application layer and the live stream

- **Status:** Accepted
- **Date:** 2026-10-16
- **Deciders:** project author
- **Context:** Phase 5 — turning the stored data into the dashboard's read API.

## Context

Phases 2–4 built the skeleton, the data layer and authentication, but the API
could only expose a caller's own credentials (`/auth/me`). The dashboard needs
*progress* reads: a student's profile and level, a time series, an activity
feed, a skills breakdown, a cohort leaderboard and a cohort summary — plus a
live feed so the UI can update without polling on a timer.

Two structural questions had to be answered: where does the *behaviour* live,
and how do we stream updates over HTTP in a way that is simple to operate and
honest about its limits.

## Decision

### 1. A thin `application/` layer appears now

ADR 0001 deliberately kept the API straight on top of the repositories (no
service layer) while the endpoints were trivial passthroughs. They no longer
are: composing a profile means reading the student, the campus, the latest
snapshot, the rank and the streak, and the same read models are shared by
several endpoints. That orchestration is application logic, not HTTP and not
SQL, so it now lives in `spd.application.analytics.AnalyticsService`.

The layer stays thin and dependency-injected: the service is constructed from
the domain repository *ports* (Protocols) in `spd.api.deps`, so it is exercised
in unit tests against in-memory fakes and never imports SQLAlchemy. This is the
same "business rules over data, boundaries at the edges" stance as before — we
are only adding it now that there is behaviour to hold.

Domain-level maths (the XP→level curve, XP velocity, streaks, rank ties) moved
into `spd.domain.progress` as pure functions, so they are tested with plain
unit tests and Hypothesis properties instead of through the database.

### 2. Read models live in the domain

`spd.domain.readmodels` defines the shapes the API returns — `StudentProgress`,
`StudentProfile`, `LeaderboardRow`, `SkillLevelView`, `ActivityItem`,
`CohortSummary`. They are the contract between the application layer and the
repositories, and they let the SQL layer return exactly what is needed instead
of leaking ORM rows upward. Mappers in `spd.infrastructure.mappers` convert ORM
entities to these models.

### 3. A complete but small set of endpoints

| Endpoint | Who | Returns |
| --- | --- | --- |
| `GET /students` | staff/admin | a page of student accounts |
| `GET /students/{login}` | owner or staff/admin | profile, rank, level progression |
| `GET /students/{login}/progress` | owner or staff/admin | daily time series (`since`/`until`) |
| `GET /students/{login}/activity` | owner or staff/admin | recent activity, newest first |
| `GET /students/{login}/skills` | owner or staff/admin | skills with current levels |
| `GET /leaderboard` | any authenticated | cohort ranked by XP |
| `GET /cohort/summary` | any authenticated | aggregate cohort statistics |
| `GET /events/stream` | any authenticated | live activity as SSE |

Authorisation is owner-only for a student's own details and staff/admin for
everything: `ensure_can_view` allows staff/admins unconditionally and students
only when `principal.login` matches the path. The roster is staff/admin only,
because it enumerates every account. `GET /students/me` was left out: callers
already know their own login, and the extra alias buys nothing.

### 4. Server-Sent Events as a cursor over activity events

The live feed is SSE (`text/event-stream`), not WebSocket. It is one-directional
(server → client), fits the read-only dashboard, needs no new infrastructure,
and reconnects automatically in the browser. The stream is a **cursor over
activity events**: each poll asks for rows after the last id already delivered,
so no event is missed or repeated. `id:` frames let the browser resume from
`Last-Event-ID` after a reconnect; a periodic `: heartbeat` comment keeps idle
connections and proxies from timing out. The polling loop and heartbeat live in
`spd.application.streams.stream_activity` as a plain async generator, testable
without a server or a database.

Because an SSE connection is long-lived, **each poll opens its own short-lived
session** rather than holding the request session for the connection's
lifetime. This keeps database connections bounded under many concurrent
clients.

`EventSource` cannot set an `Authorization` header, so the SSE endpoint accepts
the access token in a `token` query parameter (`get_stream_principal`). The
trade-off — tokens can appear in access logs/referrers — is acceptable here
because the data is read-only and the access token is short-lived.

### 5. Streaming delivered as `StreamingResponse`

The endpoint returns a Starlette `StreamingResponse` over the generator, with
`Cache-Control: no-cache` and `X-Accel-Buffering: no` so reverse proxies do not
buffer the stream.

## Consequences

- **Positive:** orchestration is unit-tested against fakes; SQL is tested
  against a real PostgreSQL via testcontainers.
- **Positive:** the domain maths is pure and property-tested with Hypothesis.
- **Positive:** SSE needs no new services and degrades gracefully (clients can
  fall back to `?since` polling if the stream drops).
- **Negative:** a thin service layer is indirection; when a route is a single
  repository call it now hops through the service. Acceptable for the shared
  read models it enables.
- **Negative:** the leaderboard derives ranks in Python over the full cohort
  rather than in SQL — fine for a demo cohort, but a materialised view/`RANK()`
  is the scaling step, deliberately deferred.
- **Negative:** tokens in query strings for SSE; mitigated by the short access
  lifetime and read-only scope.

## Alternatives considered

- **A `service`/`crud` package per model** — more ceremony and duplication than
  the handful of read compositions need.
- **Deriving progress/leaderboard purely in SQL, or a materialised view** —
  faster at scale, but moves the same logic away from the tested domain and adds
  refresh machinery; YAGNI for this cohort size.
- **WebSocket** — bidirectional transport with more moving parts (framing,
  handshake, backpressure) for a one-way feed.
- **Long-polling** — simplest transport, but worse latency and more request
  churn than SSE's restore-and-resume model.
- **`GET /students/me`** — a convenience alias that duplicates `{login}` once
  the caller already knows their own login.
