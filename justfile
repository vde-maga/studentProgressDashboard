# Student Progress Dashboard — task runner
# All recipes assume you are inside `nix develop`.

set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

# ── Setup ────────────────────────────────────────────────────────────

setup: ## Install dependencies (backend + frontend + git hooks)
    @if [ -f backend/pyproject.toml ]; then uv sync --project backend; fi
    @if [ -f frontend/package.json ]; then pnpm install --dir frontend; fi
    @pre-commit install
    @echo "✓ setup complete"

# ── Dev ──────────────────────────────────────────────────────────────

dev: ## Run backend + frontend together (frontend only if scaffolded)
    @if [ -f frontend/package.json ]; then \
        just dev-backend & just dev-frontend & wait; \
    else \
        echo "frontend not scaffolded yet — running backend only"; \
        just dev-backend; \
    fi

dev-backend: ## Run the API (reload)
    @cd backend && uv run uvicorn spd.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run the Vite dev server
    @cd frontend && pnpm dev

# ── Quality ──────────────────────────────────────────────────────────

lint: lint-backend lint-frontend ## Lint everything

lint-backend:
    @if [ -d backend ]; then \
        ruff check backend/; \
        ruff format --check backend/; \
        cd backend && uv run mypy; \
    fi

lint-frontend:
    @if [ -f frontend/package.json ]; then \
        pnpm --dir frontend exec tsc --noEmit; \
        pnpm --dir frontend lint; \
    fi

fmt: ## Format everything (nix fmt = ruff + prettier + nixfmt)
    nix fmt

# ── Tests ────────────────────────────────────────────────────────────

test: test-backend test-frontend ## Run all tests

test-backend:
    @cd backend && uv run pytest

test-integration: ## Run integration tests (needs a container engine)
    @cd backend && uv run pytest -o addopts="" -m integration

test-frontend:
    @if [ -f frontend/package.json ]; then cd frontend && pnpm test; else echo "frontend not scaffolded yet"; fi

test-e2e:
    @if [ -f frontend/package.json ]; then cd frontend && pnpm test:e2e; else echo "frontend not scaffolded yet"; fi

cov: ## Coverage report (backend, gate ≥80%; includes integration tests)
    @cd backend && uv run pytest -o addopts="" -m "integration or not integration" --cov=spd --cov-report=term-missing --cov-fail-under=80

# ── Database ─────────────────────────────────────────────────────────

db-up: ## Start PostgreSQL (docker compose)
    docker-compose up -d db
    @echo "✓ postgres up on :${POSTGRES_PORT:-5432}"

db-down: ## Stop PostgreSQL
    docker-compose down

db-reset: ## Destroy and recreate the dev database
    docker-compose down -v
    docker-compose up -d db

migrate: ## Apply Alembic migrations
    @cd backend && uv run alembic upgrade head

migrate-create msg: ## Create a migration: just migrate-create "add users table"
    @cd backend && uv run alembic revision --autogenerate -m "{{msg}}"

seed: ## Seed the database with deterministic demo data
    @cd backend && uv run python -m spd.infrastructure.seed

# ── Meta ─────────────────────────────────────────────────────────────

check: ## Run nix flake checks (formatting etc.)
    nix flake check

ci: fmt lint test ## Approximate the CI pipeline locally

clean: ## Remove build artifacts and caches
    rm -rf result .direnv
    rm -rf backend/.venv backend/.mypy_cache backend/.ruff_cache backend/.pytest_cache
    rm -rf frontend/node_modules frontend/dist
    @echo "✓ clean"
