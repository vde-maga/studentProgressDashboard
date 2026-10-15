# ADR 0002 — Authentication

- **Status:** Accepted
- **Date:** 2026-10-15
- **Deciders:** project author
- **Context:** Phase 4 — authenticating API callers and gating protected routes.

## Context

The dashboard exposes student progress data, so endpoints must be able to
identify and authorise callers. Accounts already exist (`users`), but carried
no credentials: the table had no password and there was no way to obtain or
present a proof of identity. We need a scheme that is simple to operate, hard
to get wrong, and honest about what it does not yet provide.

## Decision

### 1. Argon2id for password storage

Passwords are hashed with **Argon2id** (`argon2-cffi`) via a tiny wrapper in
`spd.core.security`. Argon2 won the Password Hashing Competition and is
memory-hard, which makes offline cracking materially more expensive than
bcrypt for the same latency budget. The algorithm parameters are encoded in the
stored hash, so they can be raised later without a schema change.

Login always performs one verification, even for unknown logins: when the
account is absent we verify against a fixed dummy hash. This equalises response
time and avoids leaking account existence (user enumeration).

### 2. Stateless JWT access and refresh tokens

Tokens are signed JWTs (`pyjwt`, HS256 by default) issued by
`spd.core.security`:

- **Access token** — short-lived (15 min), carries `sub`, `login`, `role`, a
  `type` discriminator and a `jti`.
- **Refresh token** — long-lived (14 days), same shape, `type=refresh`.

The `type` claim is checked on every decode, so a refresh token can never be
presented as an access token (and vice versa). Both tokens are **stateless**:
there is no server-side session store. This keeps the deployment a single
process with no shared cache, but it also means tokens are not individually
revocable in this phase — the blast radius is bounded by the short access
lifetime. Rotation/revocation via a persisted token table is a deliberate
future step.

### 3. Bearer auth behind reusable dependencies

`spd.api.deps` provides:

- `get_current_principal` — reads the `Authorization: Bearer` header, verifies
  the token and returns a `Principal` (the decoded payload). Missing or invalid
  credentials raise `AppError(401)` with a `WWW-Authenticate: Bearer` challenge.
- `require_roles(*roles)` — a dependency factory that adds coarse authorisation
  on top, raising `403` when the principal's role is not allowed.

Repositories are also provided as dependencies (`get_account_repository`,
`get_student_repository`) so tests can override them with in-memory fakes and
the routes stay free of session plumbing.

### 4. Endpoints and secret handling

Phase 4 exposes `POST /auth/login`, `POST /auth/refresh` and `GET /auth/me`
(no public registration — accounts are seeded). Responses never include the
password hash, and tokens/passwords are never logged.

The signing secret comes from `Settings.jwt_secret`. A known, development-only
default keeps local setup zero-config, and a validator refuses to start in
`production` unless the secret is overridden with a value of at least 32
characters. The `.env` file is git-ignored; only `.env.example` (placeholders)
is committed.

### 5. Seeded demo credentials

Every seeded account shares one documented demo password. The Argon2id hash is
stored as a constant rather than recomputed, so seeding stays deterministic
(no per-run salt) and demo data reproducible, per ADR 0001. These are throwaway
credentials for synthetic data, never real accounts.

## Consequences

- **Positive:** no session infrastructure; the API stays horizontally simple.
- **Positive:** role checks are a one-liner on any route.
- **Positive:** credentials are isolated from the profile entity — the hash
  cannot leak through `Student` responses.
- **Negative:** tokens cannot be revoked before they expire (no logout-with-
  invalidation, no rotation detection). Acceptable given the 15-minute access
  lifetime; revisit with a persisted refresh-token table if needed.
- **Negative:** `role`/`login` are copied into the token, so a role change is
  only reflected after the access token is refreshed.

## Alternatives considered

- **Server-side sessions (opaque tokens + store)** — easily revocable, but adds
  state, a store and cleanup; heavier than this phase needs.
- **bcrypt** — fine and ubiquitous, but not memory-hard and has a 72-byte
  limit; Argon2id is the better default.
- **Storing refresh tokens now** — enables revocation/rotation, but introduces
  a migration, repository and reuse-detection logic before any requirement
  demands it (YAGNI).
- **OAuth2 password flow via `fastapi.security.OAuth2PasswordBearer`** — the
  documented tutorial path, but its form-encoded login and 401 semantics fit a
  JSON SPA less cleanly than plain JSON + `HTTPBearer`.
