#!/usr/bin/env bash
# Run React frontend + Python API together (development)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/src"
export AIVE_API_PORT="${AIVE_API_PORT:-9450}"
export AIVE_FRONTEND_PORT="${AIVE_FRONTEND_PORT:-9451}"

if [ ! -d ".venv" ]; then
  echo "No .venv found. Run: ./scripts/install.sh"
  exit 1
fi
. .venv/bin/activate

# Backend
python -m aive.api.server &
API_PID=$!

# Frontend
cd frontend
if [ ! -d "node_modules" ]; then
  npm install
fi
npm run dev &
WEB_PID=$!

echo ""
echo "  React UI:  http://localhost:${AIVE_FRONTEND_PORT}"
echo "  API docs:  http://127.0.0.1:${AIVE_API_PORT}/docs"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $API_PID $WEB_PID 2>/dev/null" EXIT
wait
