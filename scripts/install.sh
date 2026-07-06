#!/usr/bin/env bash
# Install Chakshu dependencies.
#
#   ./scripts/install.sh              Full install (OpenCV + video + reports, ~1–3 min)
#   ./scripts/install.sh --minimal    Fast portable install (no OpenCV, ~30–60s)
#   ./scripts/install.sh --opencv       Add OpenCV to existing venv (filters + tracking)
#   ./scripts/install.sh -y             Recreate .venv without prompts
#
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

INSTALL_MODE=full
RECREATE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --minimal) INSTALL_MODE=minimal ;;
    --opencv|--opencv-only) INSTALL_MODE=opencv-only ;;
    -y) RECREATE=1 ;;
    *) ;;
  esac
  shift
done

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

if [ "$INSTALL_MODE" = "opencv-only" ]; then
  if [ ! -d ".venv" ]; then
    echo "No .venv — run ./scripts/install.sh --minimal first"
    exit 1
  fi
  # shellcheck disable=SC1091
  . .venv/bin/activate
  echo "Installing OpenCV (pre-built wheel)..."
  pip install -q --prefer-binary opencv-python-headless==4.10.0.84
  python -c "import cv2; print('OpenCV', cv2.__version__, 'OK — filters & tracking enabled')"
  exit 0
fi

PY=$(pick_python) || {
  echo "ERROR: Need Python 3.11, 3.12, or 3.13 (not 3.14)."
  echo "  brew install python@3.12"
  echo ""
  echo "Or skip Python entirely: ./Run-Chakshu.sh docker"
  exit 1
}

echo "=== Chakshu install ($INSTALL_MODE) ==="
echo "Python: $($PY --version)"
echo ""

if [ -d ".venv" ] && [ "$RECREATE" = "0" ]; then
  echo "Using existing .venv (use -y to recreate)"
else
  rm -rf .venv
  "$PY" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

V=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
IFS=. read -r MA MI _ <<<"$V"
if [ "$MA" -ne 3 ] || [ "$MI" -lt 11 ] || [ "$MI" -gt 13 ]; then
  echo "ERROR: venv is Python $V — need 3.11–3.13."
  exit 1
fi

echo "[1/3] Upgrading pip..."
python -m pip install -q --upgrade pip wheel

if [ "$INSTALL_MODE" = "minimal" ]; then
  echo "[2/3] Minimal packages (no OpenCV)..."
  START=$(date +%s)
  pip install -q --prefer-binary -r requirements-minimal.txt
  pip install -q -e . --no-deps
  END=$(date +%s)
  echo "      Done in $((END - START))s"
  python -c "
from aive.imaging import HAS_CV2
print('      OpenCV:', 'yes' if HAS_CV2 else 'skipped (run ./scripts/install.sh --opencv to add)')
" 2>/dev/null || echo "      OpenCV: skipped"
  echo ""
  echo "=== Minimal install ready ==="
  echo "  ./Run-Chakshu.sh local"
  echo "  Add filters/tracking later: ./scripts/install.sh --opencv"
  exit 0
fi

echo "[2/4] Full packages (wheels only)..."
START=$(date +%s)
pip install -q --prefer-binary -r requirements-fast.txt
END=$(date +%s)
echo "      Done in $((END - START))s"

echo "[3/4] Installing Chakshu package..."
pip install -q -e . --no-deps

echo "[4/5] Verifying OpenCV..."
python -c "import cv2; print('      OpenCV', cv2.__version__, 'OK')"

echo "[5/6] Video support (imageio-ffmpeg)..."
pip install -q -r requirements-video.txt

echo "[6/6] Report export (PDF/DOCX)..."
pip install -q -r requirements-reports.txt
python scripts/check-media-deps.py || echo "      Warning: FFmpeg not ready"

echo ""
echo "=== Full install ready ==="
echo "  ./Run-Chakshu.sh local"
