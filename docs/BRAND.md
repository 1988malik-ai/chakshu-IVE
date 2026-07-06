# Chakshu Forensics — Brand Guide

Base artwork: **Enhance · Analyze · Detect** eye emblem (Gemini hero illustration).

## Asset tiers

| Asset | Path | Use |
|-------|------|-----|
| Hero illustration | `frontend/public/brand/hero.png` | Command Center splash |
| Logo mark (PNG crop) | `frontend/public/brand/logo-mark.png` | Sidebar icon, app icon |
| Logo mark (SVG) | `frontend/public/brand/logo-mark.svg` | Fallback before PNG sync |
| Favicon | `frontend/public/brand/favicon.svg` | Browser tab (16–32px) |

## Sync PNG crops from hero artwork

After updating the base image, run:

```bash
chmod +x scripts/sync-brand-assets.sh
./scripts/sync-brand-assets.sh path/to/hero.png
```

This copies `hero.png`, updates `logo.png`, and generates `logo-mark.png` + `favicon-*.png`.

## Logo review (your base image)

| Context | Verdict | Notes |
|---------|---------|-------|
| **Hero / marketing** | ✅ Strong | Eye + magnifier + “Enhance · Analyze · Detect” fits forensic examination |
| **Sidebar (full image)** | ❌ Too busy | Light background, fine detail lost at ~230px width |
| **Favicon 16×16** | ❌ Unreadable | Use `logo-mark` crop or SVG only |
| **Dark UI** | ⚠️ Needs card | Hero sits on light `#f4f6f8` card in Command Center; sidebar uses cropped mark on dark |

**Recommended lockup:** cropped eye emblem + **Chakshu** / **Forensics** wordmark (implemented in `BrandMark` sidebar variant).

## UI integration

- **Sidebar:** `BrandMark variant="sidebar"` — mark + wordmark + motto
- **Command Center:** `BrandMark variant="hero"` — full artwork + title
- **Constants:** `frontend/src/brand.js`
- **Styles:** `frontend/src/styles/brand.css`

## Colors (aligned with artwork)

- Cyan accent: `#38bdf8` (`--fx-accent`)
- Navy / iris: `#1e3a5f`, `#0ea5e9`
- Mint secondary: `#34d399` (`--fx-accent-2`)
