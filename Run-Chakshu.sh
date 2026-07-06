#!/usr/bin/env bash
# One-command launcher — no long dependency install required.
#
#   ./Run-Chakshu.sh          → Docker (if available) or minimal venv + dev servers
#   ./Run-Chakshu.sh docker   → Always use Docker (fully portable, ~2 min first build)
#   ./Run-Chakshu.sh local    → Force local venv (minimal install if needed)
#
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

MODE="${1:-auto}"

run_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker not found. Install Docker Desktop or run: ./Run-Chakshu.sh local"
    exit 1
  fi
  echo ""
  echo "  Chakshu (Docker — portable, all features)"
  echo "  Open: http://localhost:9450  (API + built UI on one port)"
  echo ""
  docker compose up --build
}

run_local() {
  if [ ! -d ".venv" ]; then
    echo "First run: minimal install (~30–60 seconds, no OpenCV compile)..."
    ./scripts/install.sh --minimal -y
  fi
  exec ./scripts/dev.sh
}

case "$MODE" in
  docker)
    run_docker
    ;;
  local)
    run_local
    ;;
  auto)
    if [ -d ".venv" ]; then
      exec ./scripts/dev.sh
    fi
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
      echo "No local Python env — using Docker (portable, no pip install)."
      run_docker
    else
      run_local
    fi
    ;;
  *)
    echo "Usage: ./Run-Chakshu.sh [auto|docker|local]"
    exit 1
    ;;
esac
