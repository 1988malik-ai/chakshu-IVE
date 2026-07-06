#!/usr/bin/env bash
# Run React frontend + Python API together (development)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/src"
export AIVE_API_PORT="${AIVE_API_PORT:-9450}"
export AIVE_FRONTEND_PORT="${AIVE_FRONTEND_PORT:-9451}"
export VITE_DEV_PORT="${VITE_DEV_PORT:-$AIVE_FRONTEND_PORT}"
export VITE_API_PORT="${VITE_API_PORT:-$AIVE_API_PORT}"

LOG_FILE="${AIVE_LOG_FILE:-$HOME/.ai-ive/chakshu.log}"
mkdir -p "$(dirname "$LOG_FILE")"

free_port() {
  local port="$1"
  local pids
  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    echo "Port $port in use — stopping PID(s): $pids"
    kill $pids 2>/dev/null || true
    sleep 1
  fi
}

free_port "$AIVE_API_PORT"
free_port "$AIVE_FRONTEND_PORT"

if [ ! -d ".venv" ]; then
  echo "No .venv found."
  echo "  Quick start:  ./Run-Chakshu.sh"
  echo "  Or minimal:   ./scripts/install.sh --minimal -y && ./scripts/dev.sh"
  echo "  Or Docker:      ./Run-Chakshu.sh docker"
  exit 1
fi
# shellcheck disable=SC1091
. .venv/bin/activate

echo "Starting API on port ${AIVE_API_PORT}..."
echo "  App log:   $LOG_FILE"
python -m aive.api.server &
API_PID=$!

wait_for_api() {
  local i
  for i in $(seq 1 60); do
    if curl -sf "http://127.0.0.1:${AIVE_API_PORT}/api/health" >/dev/null 2>&1; then
      return 0
    fi
    if ! kill -0 "$API_PID" 2>/dev/null; then
      echo ""
      echo "ERROR: API process exited before becoming ready."
      echo "Log: $LOG_FILE"
      echo "--- last 40 lines ---"
      tail -40 "$LOG_FILE" 2>/dev/null || true
      exit 1
    fi
    sleep 0.25
  done
  echo ""
  echo "ERROR: API did not respond on http://127.0.0.1:${AIVE_API_PORT}/api/health"
  echo "Log: $LOG_FILE"
  tail -40 "$LOG_FILE" 2>/dev/null || true
  kill "$API_PID" 2>/dev/null || true
  exit 1
}

wait_for_api
echo "API ready."

cd frontend
if [ ! -d "node_modules" ]; then
  npm install
fi
npm run dev &
WEB_PID=$!

echo ""
echo "  React UI:  http://localhost:${AIVE_FRONTEND_PORT}"
echo "  API docs:  http://127.0.0.1:${AIVE_API_PORT}/docs"
echo "  App log:   $LOG_FILE"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $API_PID $WEB_PID 2>/dev/null" EXIT
wait
