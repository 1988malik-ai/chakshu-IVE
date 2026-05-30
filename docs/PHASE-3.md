# Phase 3 — Markup Studio

**Author:** Mohit M  
**Status:** Implemented

---

## Delivered

| Requirement | Feature |
|-------------|---------|
| R-082 Multiple selection tools | Arrow, rect, line, text, measure, redact |
| R-083 Annotations + shapes | `ExamCanvas.jsx`, `/api/markup/annotations` |
| R-084 Grouped annotations | Optional `group_id` on each annotation |
| R-085 Alignment / snap guides | 10px snap + grid overlay when enabled |
| R-163 Privacy redaction | Draw redact regions → pixelate on master frame |
| R-170 / R-171 Measurement | Two-click measure + calibration + optional speed |

---

## How to use

1. Ingest image or video frame (Examination Lab or Timeline → load frame).
2. Open **Markup Studio**.
3. Select tool: **Arrow**, **Rectangle**, **Line**, **Text**, **Measure**, **Redact**.
4. Draw on the image (click-drag; text = click + prompt).
5. Enable **Snap 10px** for alignment guides.
6. Optional **Group ID** to tag related marks.
7. Set **Calibration** (pixels per cm/m) before measuring.
8. For video speed: set **Δt** between frames when using Measure.
9. **Apply to Frame** burns annotations into the examination preview.

---

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /api/markup/annotations/{media_id}` | List (+ optional `frame_index`) |
| `POST /api/markup/annotations` | Add annotation with snap |
| `DELETE /api/markup/annotations/{media_id}/{id}` | Remove |
| `POST /api/markup/render` | Burn annotations on session frame |
| `POST /api/markup/redact` | Privacy redact regions |
| `POST /api/markup/measure` | Measure + save + draw |
| `GET /api/markup/measurements/{media_id}` | Saved measurements |

---

## Next: Phase 5

Capture, real-time preview, and reference implementation examples.
