{
  description = "Student Progress Dashboard — NixOS dev environment (Python/FastAPI, React/TS, PostgreSQL)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };

        python = pkgs.python313;

        # Playwright browsers straight from the Nix store — no downloads at runtime.
        playwrightBrowsers = pkgs.playwright-driver.browsers;

        toolchain = with pkgs; [
          # ── Task runner ────────────────────────────────────────────
          just

          # ── Python ────────────────────────────────────────────────
          python
          uv
          ruff
          mypy

          # ── Node / frontend ───────────────────────────────────────
          nodejs_24
          pnpm

          # ── Database (dev server + client libs) ────────────────────
          postgresql_17
          libpq

          # ── Misc tooling ───────────────────────────────────────────
          git
          gh
          gnumake
          jq
          openssl
          pkg-config
          nixfmt
          pre-commit
          docker-client
          docker-compose
        ];

        # `nix fmt` — one formatter for the whole repo (DRY: same tools as CI).
        formatter = pkgs.writeShellApplication {
          name = "format";
          runtimeInputs = [
            pkgs.ruff
            pkgs.nixfmt
            pkgs.prettier
          ];
          text = ''
            set -euo pipefail

            if [ -d backend ]; then
              echo "→ ruff"
              ruff check --fix backend/ || true
              ruff format backend/
            fi

            echo "→ nixfmt"
            nixfmt flake.nix

            echo "→ prettier"
            prettier --write \
              --ignore-path .gitignore \
              "**/*.{md,yml,yaml,json,ts,tsx,css}" 2>/dev/null || true
          '';
        };
      in
      {
        inherit formatter;

        devShells.default = pkgs.mkShell {
          packages = toolchain;

          env = {
            # ── Playwright (NixOS-friendly) ──────────────────────────
            PLAYWRIGHT_BROWSERS_PATH = playwrightBrowsers;
            PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = "1";

            # ── PostgreSQL (dev defaults, override in .env) ──────────
            POSTGRES_USER = "spd";
            POSTGRES_PASSWORD = "spd";
            POSTGRES_DB = "spd_dev";
            POSTGRES_PORT = "5432";
          };

          shellHook = ''
            echo "┌──────────────────────────────────────────────┐"
            echo "│  Student Progress Dashboard — dev shell      │"
            echo "│  just help   ·   nix fmt   ·   nix flake check│"
            echo "└──────────────────────────────────────────────┘"

            # Container engine: docker if reachable, else the user's rootless podman socket.
            if [ -z "''${DOCKER_HOST:-}" ] && { [ ! -S /var/run/docker.sock ] || [ ! -w /var/run/docker.sock ]; }; then
              _podman_sock="''${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/podman/podman.sock"
              if [ -S "$_podman_sock" ]; then
                export DOCKER_HOST="unix://$_podman_sock"
              fi
              unset _podman_sock
            fi

            if [ -f backend/pyproject.toml ] && [ ! -d backend/.venv ]; then
              echo "→ backend: uv sync"
              uv sync --project backend --quiet
            fi

            if [ -f frontend/package.json ] && [ ! -d frontend/node_modules ]; then
              echo "→ frontend: pnpm install"
              pnpm install --dir frontend --silent
            fi
          '';
        };

        checks = {
          # Cheap, fast gate: the repo must be nixfmt-clean.
          formatting =
            pkgs.runCommand "check-formatting"
              {
                nativeBuildInputs = [
                  pkgs.nixfmt
                  pkgs.ruff
                ];
              }
              ''
                cp -r ${self} source
                chmod -R +w source
                cd source
                nixfmt --check flake.nix
                if [ -d backend ]; then
                  ruff format --check backend/
                  ruff check backend/
                fi
                touch $out
              '';
        };
      }
    );
}
