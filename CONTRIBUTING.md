# Contributing

Thanks for taking a look. This is a portfolio project, but the workflow is the
one I would use on a team, so issues and pull requests are welcome.

## Prerequisites

Everything runs inside the Nix flake, so the only host requirement is
[Nix](https://nixos.org) with flakes enabled (the reference environment is
NixOS + Lix). You do **not** need Python, Node or PostgreSQL on the host.

```bash
git clone git@github.com:vde-maga/studentProgressDashboard.git
cd studentProgressDashboard
nix develop          # or: direnv allow
just setup           # backend + frontend deps and the pre-commit hooks
```

## Day-to-day

| Task                | Command                      |
| ------------------- | ---------------------------- |
| Run the stack       | `just db-up` then `just dev` |
| Lint everything     | `just lint`                  |
| Format everything   | `just fmt`                   |
| Unit + API tests    | `just test`                  |
| Integration tests   | `just test-integration`      |
| Coverage (backend)  | `just cov`                   |
| Coverage (frontend) | `just cov-frontend`          |
| End-to-end          | `just test-e2e`              |

`just help` lists every recipe. Run `pre-commit run --all-files` before pushing;
CI runs the same formatters and checks.

## Branching and commits

- Branch off `dev` (`feat/…`, `fix/…`, `docs/…`, `chore/…`) and open a PR back
  into `dev`. `dev` is the integration branch; `main` only ever receives
  merged `dev` (a release).
- Both `dev` and `main` are protected: a PR, a green CI run and resolved
  conversations are required.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org)
  and PRs are squash-merged, so keep the history clean and scoped.

## Tests

- **Unit** — fast, no external services (domain maths, mappers, hooks, pure
  components).
- **Integration** — real PostgreSQL via testcontainers (repositories, routes,
  auth, SSE).
- **End-to-end** — Playwright against the seeded stack.

Add or update tests with your change. Both coverage gates (backend ≥80%,
frontend thresholds in `frontend/vite.config.ts`) must stay green.

## Architecture decisions

Non-obvious choices live in [`docs/adr/`](docs/adr) as numbered ADRs. If your
change introduces a trade-off worth explaining, add the next-numbered ADR and
link it from [`docs/architecture.md`](docs/architecture.md).
