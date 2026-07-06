#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/src"
export AIVE_API_PORT="${AIVE_API_PORT:-9450}"
export AIVE_FRONTEND_PORT="${AIVE_FRONTEND_PORT:-9451}"
export VITE_DEV_PORT="${VITE_DEV_PORT:-$AIVE_FRONTEND_PORT}"
export VITE_API_PORT="${VITE_API_PORT:-$AIVE_API_PORT}"

free_port() {
  local port="$1"
  local pids
  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    echo "Stopping port $port (PID $pids)"
    kill $pids 2>/dev/null || true
    sleep 1
  fi
}

free_port "$AIVE_API_PORT"
free_port "$AIVE_FRONTEND_PORT"

# shellcheck disable=SC1091
. .venv/bin/activate

echo "Starting API on :$AIVE_API_PORT..."
nohup python -m aive.api.server > /tmp/chakshu-api-restart.log 2>&1 &
API_PID=$!
echo "API PID $API_PID"

for i in $(seq 1 40); do
  if curl -sf "http://127.0.0.1:${AIVE_API_PORT}/api/health" >/dev/null; then
    echo "API ready (${i}s)"
    break
  fi
  sleep 0.5
done

cd frontend
echo "Starting UI on :$AIVE_FRONTEND_PORT..."
nohup npm run dev -- --host 127.0.0.1 --port "$AIVE_FRONTEND_PORT" > /tmp/chakshu-ui-restart.log 2>&1 &
UI_PID=$!
echo "UI PID $UI_PID"
sleep 4

curl -sf "http://127.0.0.1:${AIVE_API_PORT}/api/health" | head -c 200
echo ""
curl -s -o /dev/null -w "UI HTTP %{http_code}\n" "http://127.0.0.1:${AIVE_FRONTEND_PORT}/"
echo ""
echo "  UI:  http://localhost:${AIVE_FRONTEND_PORT}"
echo "  API: http://127.0.0.1:${AIVE_API_PORT}/api/health"
