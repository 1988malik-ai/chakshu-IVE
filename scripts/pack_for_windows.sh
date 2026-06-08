#!/usr/bin/env bash
# Create minimal zip for Windows — run on Mac after prefetch_windows_assets.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT="$ROOT/chakshu-windows-port.zip"

echo "=== Packing minimum Windows port ==="

zip -r "$OUT" \
  Setup-Chakshu.bat \
  Run-Chakshu.bat \
  Build-Chakshu.bat \
  Install-Prerequisites.bat \
  pyproject.toml \
  requirements-fast.txt \
  requirements-video.txt \
  requirements-reports.txt \
  config \
  src \
  scripts/install.ps1 \
  scripts/install_prerequisites.ps1 \
  scripts/run_windows.ps1 \
  scripts/build_windows.ps1 \
  scripts/aive-api.spec \
  scripts/check-media-deps.py \
  desktop/main.js \
  desktop/preload.js \
  desktop/package.json \
  frontend/package.json \
  frontend/index.html \
  frontend/vite.config.js \
  frontend/public \
  frontend/src \
  -x "*.pyc" -x "*__pycache__*" -x "*.DS_Store"

if [ -d frontend/dist ]; then
  zip -r "$OUT" frontend/dist
  echo "  + frontend/dist (pre-built UI)"
fi

if [ -d packaging/wheels/win-py312 ]; then
  zip -r "$OUT" packaging/wheels/win-py312
  echo "  + packaging/wheels (offline pip)"
fi

echo ""
echo "Created: $OUT"
ls -lh "$OUT"
echo "Copy this one file to Windows, unzip, then Setup-Chakshu.bat"
