#!/usr/bin/env python3
"""Generate a skewed document photo for perspective-correction testing."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "examples" / "perspective-test"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def make_document(w: int = 900, h: int = 1200) -> Image.Image:
    img = Image.new("RGB", (w, h), (252, 250, 245))
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 42)
        body_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 24)
        mono_font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 20)
    except OSError:
        title_font = body_font = mono_font = ImageFont.load_default()

    draw.rectangle((36, 36, w - 36, h - 36), outline=(180, 175, 165), width=3)
    draw.text((72, 72), "FORENSIC EXAMINATION REPORT", fill=(25, 35, 55), font=title_font)
    draw.line((72, 140, w - 72, 140), fill=(120, 130, 150), width=2)

    lines = [
        "Case reference: CHK-2026-0042",
        "Evidence item: Document capture sample",
        "Examiner: Test Operator",
        "Date: 2026-06-02",
        "",
        "This synthetic document is intentionally skewed to test",
        "perspective / keystone correction in Examination Lab.",
        "",
        "Drag the four corners onto the white page edges,",
        "then click Preview or Apply correction.",
    ]
    y = 170
    for line in lines:
        draw.text((72, y), line, fill=(45, 55, 70), font=body_font)
        y += 34

    for row in range(6):
        for col in range(8):
            x0 = 72 + col * 92
            y0 = y + row * 28
            draw.rectangle((x0, y0, x0 + 80, y0 + 18), outline=(190, 195, 205))

    draw.text((72, h - 90), "CONFIDENTIAL — LAB USE ONLY", fill=(150, 40, 40), font=mono_font)
    return img


def skew_document(doc: Image.Image) -> Image.Image:
    w, h = doc.size
    canvas = Image.new("RGB", (w + 200, h + 160), (58, 52, 46))
    x0, y0 = 100, 80
    canvas.paste(doc, (x0, y0))

    # Map skewed quadrilateral back to axis-aligned output (inverse of camera perspective)
    src_quad = (
        x0 + w * 0.12, y0 + h * 0.06,
        x0 + w * 0.96, y0 + h * 0.02,
        x0 + w * 0.88, y0 + h * 0.94,
        x0 + w * 0.04, y0 + h * 0.90,
    )
    dst_quad = (0, 0, canvas.width, 0, canvas.width, canvas.height, 0, canvas.height)
    return canvas.transform(canvas.size, Image.Transform.QUAD, src_quad, Image.Resampling.BICUBIC)


def main() -> None:
    doc = make_document()
    flat_path = OUT_DIR / "document-flat.png"
    doc.save(flat_path)

    skewed = skew_document(doc)
    skewed_path = OUT_DIR / "document-skewed.jpg"
    skewed.save(skewed_path, quality=92)

    print(f"Flat reference:    {flat_path}")
    print(f"Skewed test photo: {skewed_path}")


if __name__ == "__main__":
    main()
