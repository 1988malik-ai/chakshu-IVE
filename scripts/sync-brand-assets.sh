#!/usr/bin/env bash
# Sync hero artwork into frontend/public/brand and generate PNG crops for favicon.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/frontend/public/brand"
SRC="${1:-}"

if [[ -z "$SRC" ]]; then
  for candidate in \
    "$ROOT/../.cursor/projects/Users-mm-home-Projects-veridetect/assets/Gemini_Generated_Image_jdytzajdytzajdyt-53c8812c-9379-4b7f-9422-305837e73a5e.png" \
    "$HOME/.cursor/projects/Users-mm-home-Projects-veridetect/assets/Gemini_Generated_Image_jdytzajdytzajdyt-53c8812c-9379-4b7f-9422-305837e73a5e.png"; do
    if [[ -f "$candidate" ]]; then SRC="$candidate"; break; fi
  done
fi

if [[ -z "$SRC" || ! -f "$SRC" ]]; then
  echo "Source image not found. Usage: $0 [path-to-hero.png]" >&2
  exit 1
fi

mkdir -p "$DEST"
cp "$SRC" "$DEST/hero.png"
cp "$SRC" "$DEST/logo.png"

python3 - "$DEST" <<'PY'
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "-q"])
    from PIL import Image

dest = Path(sys.argv[1])
hero = Image.open(dest / "hero.png").convert("RGBA")
w, h = hero.size
cx, cy = int(w * 0.50), int(h * 0.42)
size = int(min(w, h) * 0.52)
left = max(0, cx - size // 2)
top = max(0, cy - size // 2)
mark = hero.crop((left, top, left + size, top + size))
mark.save(dest / "logo-mark.png")
for s in (512, 192, 64, 32, 16):
    mark.resize((s, s), Image.Resampling.LANCZOS).save(dest / f"favicon-{s}.png")
print(f"Brand assets synced to {dest}")
PY
