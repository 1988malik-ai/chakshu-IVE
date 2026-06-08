# Phase 7 — Markup Fix, Sync, Merge, Clipboard, Subtitles

**Author:** Mohit M  
**Status:** Done

## Scope

| Area | Requirements | Changes |
|------|--------------|---------|
| Markup persistence | R-083 | Canonical `media_id`, coord scaling, burn-to-master |
| Clipboard export | R-134 | `/api/capabilities/clipboard/*` + Forensic Tools UI |
| Subtitle customization | R-121 | Styled FFmpeg burn-in |
| Stream sync | R-172 | Frame similarity + offset search |
| A/V merge & concat | R-173 | `video/merge.py` + API |

## Markup fixes

- **`annotations/media_id.py`** — resolves evidence UUID ↔ storage path
- **`annotations/store.py`** — alias-aware list/delete; scale points when frame size differs
- **`routes_markup.py`** — `persist=true` burns annotations into `master_frame`
- **UI** — `storagePath` preferred as markup key; Apply to Frame clears overlay after burn

## New API endpoints

```
GET  /api/capabilities/clipboard/frame
POST /api/capabilities/clipboard/text
POST /api/capabilities/subtitles/burn
POST /api/capabilities/merge/av
POST /api/capabilities/merge/videos
POST /api/capabilities/sync/similarity
```

## Forensic Tools UI

New panels: Clipboard Export, Subtitle Burn-in, Stream Sync & Merge, Advanced Video.

## Test

1. Markup Studio — draw arrow → visible on canvas → **Apply to Frame** → persists on seek/undo
2. Forensic Tools — Copy Frame to Clipboard
3. Burn subtitles with custom font size
4. Find Stream Offset between two clips
5. Concat Videos / Merge Video + Audio
