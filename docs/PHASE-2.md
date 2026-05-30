# Phase 2 — Video Timeline & Frame-Accurate Audio

**Author:** Mohit M  
**Status:** Implemented in current build

---

## Delivered (Phase 2)

| Requirement | Module / UI |
|-------------|-------------|
| R-073 Per-frame metadata | `analysis/frame_metadata.py` |
| R-112 Frame-accurate audio sync | `audio/player.py`, Timeline UI + video player |
| R-113 Multichannel audio probe | `audio/player.py` `probe_multichannel` |
| R-174 VFR via timestamps | `video/timeline.py` `detect_vfr` |
| R-175 Region / timestamp analysis | `frame_metadata.region_summary`, Timeline UI |
| R-051 Multi-video (partial) | `POST /api/timeline/video/secondary` |
| Video timeline UI | `VideoTimeline.jsx`, **Video Timeline** nav tab |
| Frame step prev/next/I-frame | `POST /api/timeline/step-frame` |

---

## How to use

1. Install video deps: `pip install -r requirements-video.txt`
2. Ingest or load a video (full path saved automatically on upload).
3. Open **Video Timeline** tab → **Build Timeline** (auto-runs on upload when ffprobe available).
4. Click I/P/B markers or use **Prev Frame / Next Frame / Next I-Frame**.
5. **Region Analysis** — enter start/end seconds for frame-type counts in a segment.
6. **Probe Audio Streams** — multichannel layout; **Measure A/V Offset** for sync ms.

---

## API (`/api/timeline/*`)

| Endpoint | Purpose |
|----------|---------|
| `POST /build` | Full timeline + VFR detection |
| `POST /filter` | Filter frames by type / keyframe / time range |
| `POST /region` | Region summary |
| `POST /step-frame` | Session frame step (±1 or I-frame) |
| `GET /audio/channels` | Multichannel probe |
| `GET /audio/stream-offset` | A/V start offset |
| `POST /video/secondary` | Attach additional video to session |

---

## ffprobe note

Timeline auto-falls back when ffprobe is missing:

1. **ffprobe** — full I/P/B (best)
2. **ffmpeg showinfo** — I/P/B via bundled `imageio-ffmpeg`
3. **OpenCV** — CFR frame times (types shown as `?`)

Set `AIVE_FFPROBE_PATH` for full ffprobe on macOS if desired — see `docs/FFMPEG-CROSS-PLATFORM.md`.

---

## Next: Phase 3

- Interactive annotation canvas (arrows, shapes on preview)
- Privacy redaction draw regions
- Measurement ruler on image
- Grouped annotations + alignment guides

See `docs/REQUIREMENTS-COMPLIANCE.md` roadmap.
