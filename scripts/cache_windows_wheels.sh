#!/usr/bin/env bash
# Run on Mac/Linux — downloads Windows Python packages for offline Windows setup.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY_VER="${PY_VER:-312}"
PLATFORM="${PLATFORM:-win_amd64}"
DEST="$ROOT/packaging/wheels/win-py${PY_VER}"

mkdir -p "$DEST"
echo "=== Caching packages for Windows ($PLATFORM, cp$PY_VER) ==="
echo "    -> $DEST"
echo ""

python3 -m pip install -q --upgrade pip

download_win_binary() {
  python3 -m pip download "$@" \
    --dest "$DEST" \
    --platform "$PLATFORM" \
    --implementation cp \
    --python-version "$PY_VER" \
    --only-binary=:all: \
    --no-deps
}

download_any() {
  # Universal py3-none-any wheels + sdists — no --platform / --python-version
  python3 -m pip download "$@" --dest "$DEST"
}

echo "[1/4] Windows binary wheels (numpy, OpenCV, …)..."
for pkg in \
  "numpy==2.0.2" \
  "opencv-python-headless==4.10.0.84" \
  "Pillow==10.4.0" \
  "cryptography==43.0.3" \
  "lxml" \
  "reportlab>=4.0"; do
  echo "    $pkg"
  download_win_binary "$pkg" || echo "    (warn) $pkg — will install from PyPI on Windows if needed"
done

echo "[2/4] Pure-Python wheels + build tools..."
for pkg in \
  "setuptools" \
  "wheel" \
  "pysrt==1.1.2" \
  "python-multipart==0.0.20" \
  "PyYAML==6.0.2" \
  "chardet" \
  "python-docx>=1.1"; do
  echo "    $pkg"
  python3 -m pip download "$pkg" --dest "$DEST" --only-binary=:all: --no-deps 2>/dev/null \
    || download_any "$pkg" --no-deps || true
done

echo "[3/4] FastAPI + Uvicorn (+ dependencies)..."
download_any "fastapi==0.115.6" "uvicorn==0.32.1"

echo "[4/4] Video (FFmpeg bundle)..."
download_win_binary "imageio-ffmpeg>=0.5.1" || download_any "imageio-ffmpeg>=0.5.1" --no-deps || true

WHLS=$(find "$DEST" -maxdepth 1 -name '*.whl' 2>/dev/null | wc -l | tr -d ' ')
TGZ=$(find "$DEST" -maxdepth 1 \( -name '*.tar.gz' -o -name '*.zip' \) 2>/dev/null | wc -l | tr -d ' ')
echo ""
echo "=== Done: $WHLS wheels, $TGZ source packages ==="
echo "Copy the project folder to Windows, then run Setup-Chakshu.bat"
