"""Create desktop/build/icon.png for electron-builder (Windows needs PNG/ICO, not SVG)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "desktop" / "build" / "icon.png"


def main() -> None:
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise SystemExit("Pillow required: pip install Pillow") from exc

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (256, 256), (11, 18, 32, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse([40, 88, 216, 168], outline=(61, 126, 255), width=10)
    draw.ellipse([104, 104, 152, 152], fill=(34, 197, 94))
    draw.ellipse([118, 110, 132, 124], fill=(232, 238, 247))
    img.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
