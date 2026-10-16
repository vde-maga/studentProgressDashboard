# ADR 0008 — Error handling and the SSE connection lifecycle

- **Status:** Accepted
- **Date:** 2026-10-16
- **Deciders:** project author
- **Context:** Hardening pass — making failure modes visible and bounded.

## Context

The first release was functionally complete but optimistic about failure. Two
classes of problem stood out:

- **On the frontend**, a component that threw during render blanked the whole
  document (no error boundary anywhere), queries retried deterministic `4xx`
  responses, and the profile's secondary queries (progress, skills, activity)
  failed silently — a broken chart looked the same as an empty one.
- **On the backend**, the SSE stream lived forever. A single client that never
  navigated away held a connection indefinitely, and a transient database error
  mid-stream propagated out of the generator and tore the request down with a
  stack trace instead of closing cleanly.

Neither is exotic; both are the kind of thing a reviewer notices first.

## Decision

### 1. Fail visibly on the frontend

A top-level `ErrorBoundary` (with a router `defaultErrorComponent`) renders an
`ErrorPage` when a route throws, so a render bug degrades to a recoverable page
instead of a white screen. The profile's secondary queries now render an inline
`Alert` on error rather than an empty chart.

React Query retries **transient failures only**: the retry predicate refuses any
`ApiError` with a `4xx` status and retries `5xx`/network faults once. The `401`
refresh/redirect flow already lives in the API client, so the retry loop never
needs to see it. Background query failures and mutation failures (where there is
no contextual UI) are pushed to a tiny external store and shown by a polite
live-region `Toaster`, avoiding duplicate notices for initial-load errors that
already render inline.

### 2. Bound the SSE connection

`stream_activity` accepts a `max_duration`; the endpoint passes
`sse_max_connection_seconds` (default 600). When reached, the generator ends and
the response closes. Because the stream is a cursor and `EventSource` reconnects
from `Last-Event-ID`, the cap is **invisible to clients** — they simply resume —
while keeping server-side connections finite.

The endpoint also wraps the generator: a mid-stream read failure (e.g. the
database) is logged and the connection is closed cleanly, so the browser's
automatic reconnect takes over instead of the request crashing. `CancelledError`
(client disconnect) is re-raised untouched.

## Consequences

- **Positive:** render failures and silent sub-query failures are now visible and
  recoverable; deterministic errors fail fast instead of burning retries.
- **Positive:** SSE resource usage is bounded and DB outages degrade to a clean
  reconnect rather than a crash.
- **Negative:** a bounded stream means periodic reconnections and a re-`SELECT`
  of the head cursor — negligible at this scale.
- **Negative:** the `Toaster` is a small hand-rolled store instead of a toast
  library; acceptable given there is exactly one notice type today.
