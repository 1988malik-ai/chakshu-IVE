# Phase 8 — Localization & Accessibility (R-100, R-101)

**Product:** Chakshu  
**Date:** 2026-05-29  

## R-100 — Multilingual support

- **Locales:** English + **हिन्दी (Hindi)**, **मराठी (Marathi)**, **ગુજરાતી (Gujarati)** — Indian regional languages for courts and labs
- **Backend:** `src/aive/i18n/forensic_strings.py`, `GET /api/i18n/locales`, `GET /api/i18n/{locale}`
- **UI:** `frontend/src/i18n/LocaleContext.jsx` — sidebar language selector + Settings page
- **Reports:** `locale` on `POST /api/reports/generate`; HTML/PDF labels translated via `Translator`

## R-101 — Accessibility

- **High contrast** — `data-high-contrast` CSS theme
- **Color-blind modes** — protanopia, deuteranopia, tritanopia palette overrides
- **Font scale** — 100–150% via `--fx-font-scale`
- **Reduce motion** — disables animations/transitions
- **Focus outlines** — enhanced `:focus-visible` rings
- **API:** `GET /api/accessibility/options`, `GET /api/accessibility/theme`

## Verification

1. Start API + UI; open sidebar language selector or **Settings**.
2. Switch to **हिन्दी (Hindi)** — navigation and actions show Devanagari text.
3. Switch to **मराठी (Marathi)** or **ગુજરાતી (Gujarati)** — labels update in the correct script.
4. Generate report with `locale: hi` (or `mr` / `gu`) — HTML/PDF section headers localized.
5. Enable **High contrast** and increase **Text size** — UI remains readable in Indic scripts.
