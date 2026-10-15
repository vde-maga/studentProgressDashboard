# ADR 0004 — Frontend foundation: tooling, routing and the design language

- **Status:** Accepted
- **Date:** 2026-10-16
- **Deciders:** project author
- **Context:** Phase 6 — standing up the SPA that will consume the read API.

## Context

Through phase 5 the project was an API with tests. The dashboard itself — the
thing the project is named after — did not exist. This ADR records the
foundational choices for the web client: the build tool, the routing and data
libraries, the API boundary, and the visual language. It deliberately stops
short of the pages' content (phase 7); it only fixes the skeleton they will
hang from.

The constraints carried over from the earlier phases are: a single Nix
toolchain for the whole repo (ADR 0001's "one dev shell"), strict typing as a
quality gate, and no real secrets in the repository.

## Decision

### 1. Vite + React 19 + TypeScript, managed by pnpm

Vite is the build tool and dev server: fast HMR, a first-class Vitest
integration, and a tiny config. React 19 with the function-component model is
the app runtime. TypeScript is run in `strict` mode, extended with
`noUncheckedIndexedAccess`, `verbatimModuleSyntax` and `noUnusedLocals`, so
"undefined" and unused code are caught at `tsc --noEmit` time — the same "fail
the build on a class of mistakes" stance the backend takes with `mypy --strict`.

pnpm is the package manager (content-addressed store, strict dependency
isolation, a lockfile that CI installs with `--frozen-lockfile`). Node 24 and
pnpm come from the flake, so the frontend needs no separate version manager.

TypeScript is pinned to 5.9 — _not_ the latest 7.x — because `typescript-eslint`
still declares a peer range of `<6.1.0`. Choosing a toolchain whose lint layer
supports the compiler matters more than running the newest compiler.

### 2. TanStack Router (code-based) and TanStack Query

TanStack Router gives type-safe routes and first-class data loading without a
framework. Routes are declared in **code**, not via a file-based/Vite plugin:
this keeps the route tree reviewable in one file and avoids a code-generation
step in the build and in CI.

The tree uses a pathless layout route (`id: 'app'`) that renders the app chrome
(`AppShell`) with an `<Outlet />`; `/login` sits _outside_ it so the sign-in
screen has no navigation. Protected routes are wrapped in `<RequireAuth>`,
which redirects to `/login` while anonymous.

TanStack Query owns all server state: caching, deduplication, retry and
background refresh. Components never call `fetch` directly; they call typed
endpoint functions through `useQuery`.

### 3. One thin, typed API client at the boundary

`shared/api/client.ts` is the _only_ place that talks HTTP. It:

- prefixes every request with the versioned API base (`/api/v1`);
- attaches the bearer token from `localStorage`;
- maps RFC 7807 problem responses (`{ code, detail, ... }`) to a typed
  `ApiError`;
- on a `401`, refreshes the token **once** (single-flight, so concurrent
  requests share one refresh) and retries, clearing the session and emitting a
  `spd:unauthorized` event if the refresh fails.

Endpoint functions in `shared/api/endpoints.ts` are the typed surface the UI
uses. API response types in `shared/api/types.ts` mirror the Pydantic models;
notably, `Decimal` fields (`level`, `level_progress`, `average_level`) arrive
as **strings** — Pydantic serialises decimals as strings to preserve precision
— and are parsed only for display.

Tokens live in `localStorage`: shared across tabs and reloads, at the cost of
XSS exposure. Accepted because the app injects no untrusted HTML and the access
token is short-lived.

### 4. A "ligne claire × brutalism" design language

The look is flat fills, high-contrast ink, heavy 2–3px outlines, hard offset
shadows, zero radii, and an unapologetic 4px grid — the clarity of _ligne
claire_ executed with brutalist weight. It is expressed once as **CSS custom
properties** in `shared/styles/tokens.css` (palette, spacing scale, type scale,
borders, depth, motion) and consumed by CSS-module components. No CSS-in-JS and
no utility framework: tokens plus colocated modules keep the styling portable
and dependency-free.

Motion is minimal and disabled under `prefers-reduced-motion`. Semantic HTML
and `:focus-visible` rings are non-negotiable.

### 5. Testing with Vitest + Testing Library

Vitest (sharing Vite's config and alias) runs unit tests in `jsdom` with
`@testing-library/react`. Tests target behaviour — the API client's auth/refresh
and error mapping, the formatters, and a page rendering real data through a
mocked endpoint — not implementation detail. `tsc`, ESLint and the tests are all
wired into `just` and run in CI.

## Consequences

- **Positive:** strict types from the database row to the React prop; the API
  contract is checked in one place.
- **Positive:** one toolchain (flake) builds and tests backend and frontend
  identically in dev and CI.
- **Positive:** the design language is centralised in tokens, so restyling is a
  single-file change and components stay consistent.
- **Negative:** the bundle is ~100 kB gzip for a skeleton (React + Router +
  Query); code-splitting per route is the deferred fix.
- **Negative:** token storage in `localStorage` is not httpOnly-cookie-safe;
  acceptable for a read-mostly demo, revisit if the app ever mutates heavily.
- **Negative:** TanStack's `activeProps` merge className by concatenation, a
  small papercut documented in `AppShell`.

## Alternatives considered

- **Next.js** — server rendering and a larger runtime we do not need for an
  authenticated, API-backed SPA; it would also pull the boundary away from the
  plain typed client.
- **File-based routing plugin** — ergonomic, but adds a build-time codegen step
  and a generated tree to keep in sync; code-based routing stays explicit.
- **Redux Toolkit / Zustand for server state** — reimplementing caching,
  deduplication and retries that TanStack Query already provides.
- **Tailwind / CSS-in-JS** — a build-time class pipeline or a runtime cost, when
  a small set of design tokens plus CSS modules covers the same ground.
- **TypeScript 7** — newest, but the lint layer (`typescript-eslint`) does not
  yet accept it; 5.9 keeps the whole toolchain coherent.
