# ADR 0005 — Student profile, hand-built SVG charts and the live feed

- **Status:** Accepted
- **Date:** 2026-10-16
- **Deciders:** project author
- **Context:** Phase 7 — turning the read API and SSE stream into the actual
  dashboard views.

## Context

Phase 6 delivered the shell: routing, a typed client, an auth session and a
design system. The product, however, is the _student profile_ — XP and level,
a progress-over-time chart, a skills breakdown and a live activity feed — plus
a cohort leaderboard and live cohort activity on the dashboard. That raised
three questions: how to compose several reads on one screen, how to draw the
charts, and how to consume the event stream without it fighting the REST data.

## Decision

### 1. Compose reads with TanStack Query, gated on the profile

The profile screen needs four reads (`profile`, `progress`, `skills`,
`activity`). Each is its own `useQuery` with a stable, hierarchical key
(`['student', login, 'profile']`, …). The secondary three are `enabled` only
once the profile query succeeds, so a forbidden or missing student short-circuits
to a single error state instead of four failing requests.

Error states are first-class: a `403` renders "you can only view your own
profile" (with a link to the caller's own), a `404` renders a not-found message,
and anything else falls back to the API's problem detail. Authorization is
enforced by the API; the client only chooses the right message.

### 2. Charts are hand-built SVG, with the maths in a pure module

The charts (line/area, radar, progress bar) are small SVG components built
directly, not a charting dependency. The geometry — scaling a series into a
box, turning points into path strings, laying out radar spokes and rings —
lives in `shared/charts/geometry.ts` as pure functions and is unit-tested
without rendering. Components only map data to `<svg>` elements styled from the
design tokens.

Rationale: a charting library is a large, themeable dependency for three simple
shapes; hand-built SVG stays on-brand (hard strokes, flat fills) and keeps the
interesting logic testable in isolation. This mirrors the backend's "pure
domain, thin edges" stance.

### 3. The live feed is a de-duplicating append on top of REST history

`GET /events/stream` is a cursor over activity events (ADR 0003).
`useActivityStream` opens an `EventSource`, listens for each activity kind,
and keeps a bounded, de-duplicated list (newest first) of what it has seen;
`EventSource` reconnects on its own and resumes from `Last-Event-ID`. On the
profile the live events are filtered by `student_login` and **merged with the
REST activity history** by id, so the list is complete on load and stays live
afterwards without duplication. The dashboard shows the same stream across the
whole cohort.

The connection is always torn down on unmount. A "● live" marker reflects the
connection state (`open` vs `connecting`) without pretending to be authoritative.

## Consequences

- **Positive:** every read is cacheable, retryable and independently testable;
  keys make invalidation obvious later.
- **Positive:** the chart maths is proven by fast unit tests; no chart
  dependency to audit or theme.
- **Positive:** the feed degrades gracefully — if SSE is unavailable from the
  UI it can fall back to polling without changing the page (the API already
  supports `?since`).
- **Negative:** merging REST and live activity is application logic in a
  component; it is factored into a small pure helper, but it is still
  bookkeeping the API could own by returning a resumable history endpoint.
- **Negative:** hand-built charts re-implement axes/tooltips if the needs grow;
  acceptable while the visuals are intentionally bespoke.
- **Negative:** `EventSource` cannot send headers, so the token rides in the
  query string (see ADR 0003); a hostile proxy logging URLs could capture it,
  bounded by the short access-token lifetime.

## Alternatives considered

- **A charting library (Recharts/Visx/Chart.js)** — ergonomic, but a heavy,
  opinionated dependency for three shapes we want to style ourselves.
- **One big profile query (`Promise.all` in a loader)** — fewer hooks, but
  coarser caching, all-or-nothing failures and no independent refetch.
- **WebSocket or polling for the feed** — SSE is already the backend's choice
  and the browser reconnects for free.
- **Rendering the stream directly without REST history** — the list would start
  empty on every mount until the next event; merging history gives an instantly
  useful screen.
