#!/usr/bin/env bash
# Fast install (~1–3 min on Python 3.12). Uses wheels only — no compiling OpenCV.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

pick_python() {
  for cmd in python3.12 python3.13 python3.11; do
    if command -v "$cmd" >/dev/null 2>&1; then
      ver=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
      IFS=. read -r major minor _ <<<"$ver"
      if [ "$major" -eq 3 ] && [ "$minor" -ge 11 ] && [ "$minor" -le 13 ]; then
        echo "$cmd"
        return 0
      fi
    fi
  done
  return 1
}

PY=$(pick_python) || {
  echo "ERROR: Need Python 3.11, 3.12, or 3.13 (not 3.14)."
  echo "  brew install python@3.12"
  exit 1
}

echo "=== AI-IVE fast install ==="
echo "Python: $($PY --version)"
echo ""

RECREATE=0
if [ -d ".venv" ]; then
  if [ "${1:-}" = "-y" ] || [ "${RECREATE_VENV:-}" = "1" ]; then
    RECREATE=1
  else
    echo "Tip: run './scripts/install.sh -y' to recreate .venv without prompts"
    echo "Using existing .venv"
  fi
fi

if [ "$RECREATE" = "1" ] || [ ! -d ".venv" ]; then
  rm -rf .venv
  "$PY" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

V=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
IFS=. read -r MA MI _ <<<"$V"
if [ "$MA" -ne 3 ] || [ "$MI" -lt 11 ] || [ "$MI" -gt 13 ]; then
  echo "ERROR: venv is Python $V — need 3.11–3.13. Delete .venv and run again."
  exit 1
fi

echo "[1/4] Upgrading pip..."
python -m pip install -q --upgrade pip wheel

echo "[2/4] Installing packages (wheels only, no ONNX)..."
START=$(date +%s)
pip install -q --prefer-binary -r requirements-fast.txt
END=$(date +%s)
echo "      Done in $((END - START))s"

echo "[3/4] Installing AI-IVE package..."
pip install -q -e . --no-deps

echo "[4/5] Verifying OpenCV..."
python -c "import cv2; print('      OpenCV', cv2.__version__, 'OK')"

echo "[5/6] Installing cross-platform video support (imageio-ffmpeg)..."
pip install -q -r requirements-video.txt

echo "[6/6] Installing report export (PDF/DOCX)..."
pip install -q -r requirements-reports.txt
python scripts/check-media-deps.py || echo "      Warning: FFmpeg not ready — see docs/FFMPEG-CROSS-PLATFORM.md"

echo ""
echo "=== Finished ==="
echo "  source .venv/bin/activate"
echo "  export PYTHONPATH=src"
echo "  python -m aive.api.server"
echo ""
echo "Optional AI models (slow, ~100MB): pip install -r requirements-ai.txt"
