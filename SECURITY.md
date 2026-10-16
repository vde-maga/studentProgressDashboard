# Security Policy

## Reporting a vulnerability

Please report suspected vulnerabilities privately through GitHub's
[Security advisories](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
("Report a vulnerability" under the repository's **Security** tab) rather than
opening a public issue. I aim to acknowledge reports within a few days.

## Scope

This project is a **portfolio demo, not a production deployment**. Its security
posture is documented and deliberately bounded in
[ADR 0007](docs/adr/0007-scope-and-deployment.md). In particular, the following
are known and accepted for the demo, and are **not** vulnerability reports:

- **Stateless, non-revocable tokens.** A leaked access/refresh token is valid
  until it expires; there is no denylist ([ADR 0002](docs/adr/0002-authentication.md)).
- **SSE token in the query string.** Because `EventSource` cannot set headers,
  the access token travels as `?token=…`, which a hostile proxy could log
  ([ADR 0003](docs/adr/0003-analytics-and-sse.md)).
- **Seeded demo credentials.** The seeded accounts share the password
  `42cursus!`; they exist only to make the demo reproducible.
- **No rate limiting, WAF or production observability** are wired up.

Reports that are in scope include, for example: authentication or
authorization bypasses (e.g. a student reading another student's detail data),
injection, and dependency vulnerabilities with a viable exploit path.

## Dependency scanning

CI runs a non-blocking `audit` job (`pip-audit` and `pnpm audit`), and
Dependabot watches `uv.lock`, `pnpm-lock.yaml`, GitHub Actions and the Nix
flake inputs.
