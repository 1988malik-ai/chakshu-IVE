#!/usr/bin/env bash
# Mac one-shot: cache Windows Python wheels + build portable frontend dist.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== 1/2 Windows Python wheels ==="
bash "$ROOT/scripts/cache_windows_wheels.sh"

echo ""
echo "=== 2/2 Frontend build (portable static files) ==="
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then npm install; fi
npm run build
echo "    -> frontend/dist (copy to Windows with the project)"

echo ""
echo "=== Ready to copy to Windows ==="
echo "  - packaging/wheels/win-py312/"
echo "  - frontend/dist/"
echo "On Windows: Setup-Chakshu.bat (faster pip) then Run-Chakshu.bat"
