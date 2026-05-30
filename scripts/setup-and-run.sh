#!/usr/bin/env bash
# One script: install (fast, no OpenCV) + start API + React UI
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== AI-IVE setup ==="

# Find any Python 3.10+
PY=""
for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    if "$cmd" -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
      PY=$cmd
      break
    fi
  fi
done
if [ -z "$PY" ]; then
  echo "ERROR: Need Python 3.10+. Install from https://www.python.org/downloads/"
  exit 1
fi

echo "Python: $($PY --version)"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  "$PY" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing packages (fast, ~30 seconds)..."
python -m pip install -q --upgrade pip
pip install -q --no-cache-dir -r requirements-minimal.txt
pip install -q -e . --no-deps

python -c "
from aive.imaging import HAS_CV2
print('OpenCV:', 'yes' if HAS_CV2 else 'no (images still work via Pillow)')
"

export PYTHONPATH="$ROOT/src"
export AIVE_API_PORT="${AIVE_API_PORT:-9450}"
export AIVE_FRONTEND_PORT="${AIVE_FRONTEND_PORT:-9451}"

echo ""
echo "=== Starting AI-IVE ==="
echo "  UI:  http://localhost:${AIVE_FRONTEND_PORT}"
echo "  API: http://127.0.0.1:${AIVE_API_PORT}/docs"
echo ""

python -m aive.api.server &
API_PID=$!

cd frontend
if [ ! -d "node_modules" ]; then
  echo "Installing frontend (npm)..."
  npm install --silent
fi
npm run dev &
WEB_PID=$!

trap 'kill $API_PID $WEB_PID 2>/dev/null; exit' INT TERM EXIT
wait
