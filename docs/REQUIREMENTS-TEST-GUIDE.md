# Chakshu — Requirements Test Guide

**Document:** How to test each requirement (R-001 … R-196)  
**Author:** Mohit M  
**Product:** Chakshu (AI-IVE)  
**Version:** 1.0.0  
**Date:** 2026-05-29  
**Companion:** `docs/REQUIREMENTS-COMPLIANCE.md`  
**Workflow testing:** [`docs/WORKFLOW-TEST-GUIDE.md`](WORKFLOW-TEST-GUIDE.md) — end-to-end scenarios WF-01 … WF-12

This guide maps **every tracked requirement** to concrete UI steps, API calls, and pass criteria. Use it for QA, procurement demos, and release sign-off.

---

## 1. Before you test

### 1.1 Start the stack

```bash
# Terminal 1 — API
cd ~/Desktop/AI-IVE
source .venv/bin/activate
export PYTHONPATH=src
python -m aive.api.server

# Terminal 2 — UI
cd ~/Desktop/AI-IVE/frontend
npm run dev
```

| Service | URL |
|---------|-----|
| React UI | http://127.0.0.1:9451 |
| API + Swagger | http://127.0.0.1:9450/docs |
| Health check | http://127.0.0.1:9450/api/health |

### 1.2 Prerequisites

| Check | Command / action | Expected |
|-------|------------------|----------|
| OpenCV | `curl -s http://127.0.0.1:9450/api/health \| python3 -m json.tool` | `"opencv": true` |
| FFmpeg | same | `"ffmpeg": true` |
| License | UI loads without block, or `GET /api/license/status` | `valid: true` or trial active |

Install gaps: `./scripts/install.sh -y` (Python **3.12**), `brew install ffmpeg`.

### 1.3 Test artifacts (prepare once)

| File | Use |
|------|-----|
| `sample.jpg` | Image filters, markup, hash |
| `sample.mp4` (5–30 s, H.264) | Video timeline, seek, export, audio |
| `sample.srt` | Subtitle burn-in |
| `sample.aac` or `.wav` | Audio mux / merge |
| Second clip `sample-b.mp4` | Stream sync, compare, concat |
| Folder of numbered `.jpg` | Sequence → video |

Set paths in **Examination Lab → Load by Path** or **Legal Export** input fields.

### 1.4 Legend

| Column | Meaning |
|--------|---------|
| **UI** | Steps in React app (preferred for demos) |
| **API** | curl / Swagger when UI is thin or for automation |
| **Pass** | Minimum evidence requirement is met |
| **Status** | From compliance matrix: IMPLEMENTED / PARTIAL / PLANNED |

**Session helper (API tests):**

```bash
SESSION=$(curl -s -X POST http://127.0.0.1:9450/api/session | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
curl -s -X POST "http://127.0.0.1:9450/api/media/upload?session_id=$SESSION" -F "file=@/path/to/sample.jpg"
```

---

## 2. Section 1 — Core Platform

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-001** | ≥140 filters | IMPLEMENTED | UI: **Examination Lab** → filter list scroll count. API: `GET /api/filters` → check `count` ≥ 140 | Catalog lists 191 filters; `implemented_count` matches live count |
| **R-002** | Standalone operation | IMPLEMENTED | Run API + UI without external services; optional: `./scripts/setup-and-run.sh` or desktop Electron build | App loads evidence and processes locally |
| **R-003** | License protection | IMPLEMENTED | API: `GET /api/license/status`; UI shows trial/license state | Returns `machine_id`, trial or valid license |
| **R-004** | Visible filter execution | IMPLEMENTED | UI: ingest image → select **Brightness** or `adv_auto_contrast` → **Apply** | Preview visibly changes; `filter_chain` grows |

---

## 3. Section 2 — Video Decoding

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-010** | FFmpeg decoding | IMPLEMENTED | Upload / load `.mp4` by path; **Timeline Pro** builds index | Frame preview loads; no decode error |
| **R-011** | DirectShow (Windows) | PARTIAL | Windows only: load capture device or legacy adapter path; else verify FFmpeg fallback on macOS/Linux | Video still decodes via FFmpeg |
| **R-012** | Video for Windows | PARTIAL | Windows: adapter module present; cross-platform: FFmpeg fallback | Document platform; decode succeeds |
| **R-013** | QuickTime | PARTIAL | Load `.mov` if available; else confirm FFmpeg probe | Opens or clear FFmpeg error |
| **R-014** | Standard formats + codecs | IMPLEMENTED | **Settings** → Media compatibility; `GET /api/capabilities/media/formats`; export `mp4_h264` and `mkv_copy` via Legal Export / `POST /api/export` | FFmpeg/system codec source is shown; accepted extensions are listed; output files play in VLC |

---

## 4. Section 3 — Bookmarks & Projects

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-020** | Bookmarks | IMPLEMENTED | UI: **Examination Lab** or **Forensic Tools** → **Bookmarks (R-020)** → load evidence by path → scrub to a frame → fill label/notes/tags/priority/examiner → **Bookmark this frame**. Apply a filter → **Bookmark current filter** → **Go to** / **Edit** / **Delete**. API: `POST /api/bookmarks` (frame or `bookmark_type: filter` + `filter_id` + `metadata`); `GET /api/bookmarks?media_path=...`; `PATCH` / `DELETE` `/api/bookmarks/{id}` | Bookmarks persist in `~/.ai-ive/bookmarks.json`; jump restores time and filter; project workflow logs `bookmark_frame` / `bookmark_filter` |
| **R-021** | Human-readable project | IMPLEMENTED | API: `GET /api/project/current`; `POST /api/project/save`; inspect `~/.ai-ive/projects/*.aive.yaml` | YAML readable; steps recorded |
| **R-022** | Import projects | IMPLEMENTED | **Settings** → Project import → enter `.aive.yaml`, `.aive.yml`, or compatible `.json` path → **Inspect** → **Import project**; API: `POST /api/project/import/inspect`, then `/api/project/import` | Compatibility summary shows format/counts/warnings; supported project imports and becomes active |

---

## 5. Section 4 — Export (Video & Media)

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-030** | Wide export / stream copy | IMPLEMENTED | `POST /api/export` with `"use_stream_copy": true` | Output created; `-c:v copy` in command |
| **R-031** | CFR export | IMPLEMENTED | Export with `"frame_rate_mode": "cfr", "fps": 29.97` | Fixed frame rate in ffprobe |
| **R-032** | VFR export | IMPLEMENTED | Export with `"frame_rate_mode": "vfr"` | VFR flag in export command |
| **R-033** | Batch conversion | IMPLEMENTED | Run batch module / queue on folder (see `src/aive/batch/queue.py`) | Multiple outputs queued |
| **R-034** | Frames to PDF | IMPLEMENTED | **Legal Export** → PDF frame layout (page size, orientation, grid, margin, title) → Export; API: `POST /api/export/pdf-frames` | PDF exists; layout matches settings |
| **R-035** | Media bundle | IMPLEMENTED | API: `POST /api/export/media-bundle` | Original + processed in output dir |
| **R-036** | I-frame export | IMPLEMENTED | UI: **Legal Export** → I-frames; API: `POST /api/export/i-frames` | JPEGs only on I-frame indices |
| **R-037** | Trim without transcode | IMPLEMENTED | **Forensic Tools** or `POST /api/capabilities/video/trim` | Segment file; stream copy used |
| **R-038** | Frame list export | IMPLEMENTED | `POST /api/capabilities/video/export-frames` with `frame_indices: [0,10,20]` | Named frame JPEGs exported |

---

## 6. Section 5 — Images & Organization

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-040** | JPEG, PNG, TIFF, BMP | IMPLEMENTED | Ingest each format via **Ingest Evidence** | Preview loads for each |
| **R-041** | RAW formats | IMPLEMENTED | **Settings** → Media compatibility confirms RAW dependency; ingest `.dng`/`.cr2` with `rawpy` installed, or without it for diagnostics | RAW opens when `rawpy` is installed; otherwise UI shows actionable `pip install rawpy` guidance |
| **R-042** | Nested folders | IMPLEMENTED | API/library: scan folder with subdirs | All supported files listed |

---

## 7. Section 6 — Editing & Multi-Media

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-050** | Undo / Redo | IMPLEMENTED | Apply 2 filters → undo/redo via API `POST /api/edit/undo` | Preview reverts/advances |
| **R-051** | Multi-video load | PARTIAL | API: `POST /api/timeline/video/secondary` with second path | Secondary registered; full dual-view UI limited |
| **R-052** | Non-destructive master | IMPLEMENTED | Apply filters → **Reset to Original** | Original restored; `filter_chain` empty |

---

## 8. Section 7 — GPU Encoding

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-060** | GPU H.264/H.265 | IMPLEMENTED | `GET /api/gpu/encoders` | Lists NVENC/QSV/AMF if hardware present; export uses selected codec |

---

## 9. Section 8 — Stream Analysis

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-070** | Timestamp extraction | IMPLEMENTED | **Timeline Pro** → Build timeline | Frames have `pts` values |
| **R-071** | Demultiplexing | IMPLEMENTED | `POST /api/forensics/examination/analyze-video?path=...` | Returns `streams` array |
| **R-072** | I/P/B visibility | IMPLEMENTED | Same analyze + **Stream Analysis** panel I/P/B counts | Non-zero I/P/B summary |
| **R-073** | Per-frame metadata | IMPLEMENTED | Timeline click frame → metadata panel; `POST /api/timeline/filter` | Frame type, PTS shown |
| **R-074** | MPEG macroblocks | PARTIAL | **Forensic Tools** → **MPEG Macroblock Overlay** | Overlay preview; not full motion-vector suite |
| **R-075** | Advanced seek | IMPLEMENTED | **Forensic Tools**: Probe, Seek Time, Nearest I-Frame; **Timeline Pro** step frames | Correct frame at time/index |

---

## 10. Section 9 — Tracking & Annotations

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-080** | Manual/auto tracking | PARTIAL | API/tracker module CSRT/KCF on video session | Track box updates; not full UI wizard |
| **R-081** | Reuse tracking data | IMPLEMENTED | Save/load tracker JSON (`tracking/tracker.py`) | Same track after reload |
| **R-082** | Multiple markup tools | IMPLEMENTED | **Markup Studio** → Arrow, Rect, Line, Text, Measure, Redact | Each tool draws on canvas |
| **R-083** | Annotations + burn | IMPLEMENTED | Draw arrow → **Apply to Frame** → seek video | Annotation visible after burn |
| **R-084** | Grouped annotations | IMPLEMENTED | Set **Group ID** → add shapes → list groups via markup API | Same `group_id` on items |
| **R-085** | Snap / guides | IMPLEMENTED | Enable **Snap 10px** → draw near grid | Points align to 10 px grid |

**Markup API smoke test:**

```bash
curl -s -X POST http://127.0.0.1:9450/api/markup/annotations \
  -H "Content-Type: application/json" \
  -d '{"media_id":"/full/path/sample.jpg","type":"arrow","frame_index":0,"points":[[10,10],[100,100]],"image_width":1920,"image_height":1080}'
```

---

## 11. Section 10 — AI / ML

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-090** | AI enhancement | IMPLEMENTED | **Forensic Tools → AI / ML** → Apply; or filter `both_enhance_ai` | Preview improves; status shows tool applied |
| **R-091** | Custom ONNX import | IMPLEMENTED | Import `.onnx` in UI or `POST /api/ai/models/import`; `GET /api/ai/models` | Model listed; enhance with `model_id` (needs onnxruntime) |

---

## 12. Section 11 — Localization & Accessibility

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-100** | Multilingual UI | IMPLEMENTED | Sidebar **Language** → हिन्दी / मराठी / ગુજરાતી; `GET /api/i18n/hi`, `/mr`, `/gu` | Nav + reports localized in Indian languages |
| **R-101** | Accessibility | IMPLEMENTED | Sidebar a11y: high contrast, color-blind, font scale | Theme updates; readable Indic fonts (Noto) |

---

## 13. Section 12 — Audio

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-110** | Audio extraction | IMPLEMENTED | **Legal Export** → Extract audio; `POST /api/export/audio` | `.aac`/`.wav` created |
| **R-111** | Volume / mute | IMPLEMENTED | Load video → Evidence Path audio player and **Timeline Pro** synced audio/video → change volume, mute, navigate between tabs | Mute/volume persist and affect Evidence Path audio, Timeline synced audio, and timeline video playback |
| **R-112** | Frame-accurate audio | PARTIAL | **Timeline Pro** → play video + audio probe | Audio follows scrub; not sample-accurate everywhere |
| **R-113** | Multichannel | IMPLEMENTED | **Timeline Pro** → **Probe** audio channels | Channel layout returned |
| **R-114** | Audio redaction | IMPLEMENTED | **Forensic Tools** or **Timeline Pro** → **Audio Redaction** — add mute regions, export audio or video; API: `POST /api/capabilities/audio/redact` | Muted intervals in output file; workflow step + audit logged |
| **R-115** | Add audio stream | IMPLEMENTED | **Forensic Tools** or **Timeline Pro** → **Add Audio Stream (R-115)** → probe streams → set external audio + output → **Add track (keep existing)** or **Replace** → **Add audio to video**; API: `GET /api/capabilities/audio/streams`, `POST /api/capabilities/audio/mux` with `mode: add` | Output MP4 has new audio track; add mode retains original audio when present |
| **R-116** | A/V sync adjust | IMPLEMENTED | `POST /api/capabilities/audio/sync` with delay ms | Offset applied in output |
| **R-117** | Pad video to audio | IMPLEMENTED | **Add Audio Stream** with audio longer than video (e.g. 30s commentary on 17s clip) → leave **Automatically pad video** on → mux; UI shows duration compare + pad seconds; API: `GET /api/capabilities/audio/duration-compare`, `POST /api/capabilities/audio/mux` with `auto_pad_video: true` | Output video duration matches longer audio; last frame frozen for pad segment; workflow step `pad_video_to_audio` |

---

## 14. Section 13 — Subtitles & Overlays

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-120** | SRT / SMI rendering | IMPLEMENTED | **Forensic Tools** → **Subtitles — SRT & SMI** → Load & parse; **Render at playhead** or auto-overlay; API: `POST /api/capabilities/subtitles/parse`, `overlay-session` | Cues listed; text drawn on examination frame at matching times |
| **R-121** | Subtitle customization | IMPLEMENTED | Same panel → font size, margin, **Burn subtitles into video**; SMI auto-converted for FFmpeg | Burned MP4 with styled subs |
| **R-122** | Timestamp overlay | IMPLEMENTED | **Forensic Tools** → Apply Timestamp + Grid | Timestamp on preview |
| **R-123** | Grid overlay | IMPLEMENTED | Same as R-122 with `grid: true` | Grid visible on frame |
| **R-124** | Side-by-side compare | PARTIAL | **Forensic Tools** → Start Side-by-Side → Render Compare | Combined preview; limited layout options |
| **R-125** | Picture-in-Picture | PARTIAL | `POST /api/capabilities/examination/overlay` with PiP params | PiP in API; UI partial |

---

## 15. Section 14 — Reports

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-130** | HTML/PDF/DOC reports | IMPLEMENTED | **Case Reports** → set output dir, template, paper size, formats (HTML/PDF/DOCX), include settings & references → **Generate**; apply filters/exports first so workflow steps exist; `POST /api/reports/generate`; `GET /api/reports/preview` | HTML table with steps/settings/refs; PDF table; DOCX with same columns; paths listed in UI |
| **R-131** | Paper sizes | IMPLEMENTED | Generate with `paper_size`: A4, Letter, Legal, A3 | PDF page size matches |
| **R-132** | Report templates | IMPLEMENTED | Templates: standard, detailed, executive, minimal | Layout differs per template |
| **R-133** | Secure copy in reports | IMPLEMENTED | **Forensic Tools** → Secure Copy + Report, then **Case Reports** → Generate HTML/PDF/DOCX | Secure copy destination and hash report JSON are listed in the report workflow and Secure Copy Verification section |
| **R-134** | Clipboard export | IMPLEMENTED | **Forensic Tools** → Copy Frame / Copy Hashes | Clipboard receives data URL or hash text |

---

## 16. Section 15 — Forensic Integrity

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-140** | Multi-algorithm hash | IMPLEMENTED | **Forensic Tools** → Hash Evidence File | MD5, SHA-1, SHA-256, SHA-512 shown |
| **R-141** | Frame hash | IMPLEMENTED | `GET /api/capabilities/hash/frame?session_id=...` | Hash of current frame |
| **R-142** | Secure copy + report | IMPLEMENTED | **Secure Copy + Report** button | Destination file + JSON report |
| **R-143** | Chain of custody | IMPLEMENTED | Ingest evidence → **Chain of Custody** tab | INGEST / ENHANCE entries |
| **R-144** | Audit log | IMPLEMENTED | API: `GET /api/forensics/cases/{case_id}/audit` | FILTER_APPLY, ANNOTATION_ADD events |
| **R-145** | Secure media batch | IMPLEMENTED | **Legal Export** → secure media folder/batch export | Manifest and verified batch export files are created |

---

## 17. Section 16 — Advanced Processing

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-150** | Deinterlace | IMPLEMENTED | Filter `adv_deinterlace` on frame; API `POST /api/capabilities/advanced/deinterlace` | Progressive output / less combing |
| **R-151** | Lens distortion | IMPLEMENTED | Filter `geo_barrel` or `both_lens_correction` | Straight lines improved |
| **R-152** | Panoramic | PARTIAL | Filter `adv_panorama` on wide/fisheye still | Cylindrical preview only |
| **R-153** | Homomorphic | IMPLEMENTED | Filter `adv_homomorphic` | Uneven lighting flattened |
| **R-154** | Auto contrast + halo | IMPLEMENTED | Filter `adv_auto_contrast` | Contrast up; minimal halos |
| **R-155** | Color separation | IMPLEMENTED | Filter `adv_color_separate` params `channel: r` | Single channel visible |
| **R-156** | Motion deblur | IMPLEMENTED | Filter `adv_motion_deblur` or `both_deblur_ai` | Sharper edges |
| **R-157** | Multi-image align | IMPLEMENTED | **Geometry Correction** → Multi-image perspective alignment, set reference + target image paths, then align | Aligned JPEG(s) and `alignment_manifest.json` are written with homography and RMS error |
| **R-158** | Perspective stabilize | PARTIAL | Filter `adv_perspective`; API `advanced/perspective-stabilize` | Tilt reduced |
| **R-159** | Super-resolution | IMPLEMENTED | Filter `adv_super_resolution` scale 2 | Larger/sharper preview |
| **R-160** | Video stabilize | IMPLEMENTED | **Forensic Tools** → Stabilize | `stabilized.mp4` plays smoother |
| **R-161** | Frame dup FPS | IMPLEMENTED | **Forensic Tools** → Adjust FPS (e.g. 15) | Duration/fps changes |
| **R-162** | Manual FPS | IMPLEMENTED | Same API with `target_fps` | Matches requested fps |
| **R-163** | Privacy redaction | IMPLEMENTED | **Markup Studio** → Redact rectangle | Pixelated region on master |
| **R-164** | Freeze frame video | IMPLEMENTED | `POST /api/capabilities/advanced/freeze` | Static clip for duration |
| **R-165** | Reverse playback | IMPLEMENTED | **Examination Lab** or **Timeline Pro** → transport **◀◀** (reverse); optional **Forensic Tools** → Reverse (export `reversed.mp4`) | Preview steps backward frame-by-frame; stops at t=0 |
| **R-166** | JPEG artifact reduce | IMPLEMENTED | Filter `adv_jpeg_artifact` on heavy JPEG | Block edges softened |
| **R-167** | Channel invert/replace | IMPLEMENTED | Filter `adv_channel_replace` | Channel swapped/inverted |

**Advanced video API example:**

```bash
curl -s -X POST http://127.0.0.1:9450/api/capabilities/advanced/stabilize \
  -H "Content-Type: application/json" \
  -d '{"input_path":"/path/sample.mp4","output_path":"/tmp/stable.mp4"}'
```

---

## 18. Section 17 — Measurement & Analysis

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-170** | Image measurement | IMPLEMENTED | **Markup Studio** → Measure line; set calibration px/unit | Distance label shown |
| **R-171** | Speed estimation | IMPLEMENTED | Measure with **Δt** set on video frame | Speed in metadata |
| **R-172** | Stream sync | IMPLEMENTED | **Forensic Tools** → Find Stream Offset (two paths) | `recommended_offset_ms` returned |
| **R-173** | Merge / concat | IMPLEMENTED | **Merge Video + Audio** / **Concat Videos** | Output MP4 exists |
| **R-174** | VFR playback | PARTIAL | Load VFR clip → Timeline shows `vfr: true`; seek by PTS | Plays; not all players VFR-perfect |
| **R-175** | Region analysis | IMPLEMENTED | **Timeline Pro** → select region → Analyze Region | I/P/B counts for window |

---

## 19. Section 18 — Capture & Real-Time

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-180** | Live video capture | IMPLEMENTED | **Live Capture** → Start browser webcam → Snap | Frame ingested to session |
| **R-181** | Sequence → video | IMPLEMENTED | **Live Capture** → folder of images → sequence to video | MP4 created |
| **R-182** | Real-time filters | IMPLEMENTED | Live Capture → pick filter → MJPEG stream URL | Filtered live preview |
| **R-183** | Screen capture | IMPLEMENTED | **Live Capture** → Screen capture (FFmpeg) | Screen MP4 saved |

---

## 20. Section 19 — Platform & Integration

| ID | Requirement | Status | How to test | Pass criteria |
|----|-------------|--------|-------------|---------------|
| **R-190** | Windows x64 install | IMPLEMENTED | Run `build/windows/build_x64.ps1` on Windows | Installer/build artifacts |
| **R-191** | Windows x86 | PARTIAL | `build_x86.ps1` profile | Build script runs; unsupported deps may warn |
| **R-192** | Operation logging | IMPLEMENTED | Enable logging module; perform action; check log file | Entry written |
| **R-193** | VMS-compatible export | PARTIAL | Export MP4 with faststart; play in browser/VMS | `moov` at front; yuv420p |
| **R-194** | External metadata | IMPLEMENTED | **Forensic Tools** / API metadata export, ffprobe, exif | JSON bundle with streams/EXIF |
| **R-195** | Persistent notes | IMPLEMENTED | **Forensic Tools** → Save Note | Note appears on reload |
| **R-196** | Example workflows | IMPLEMENTED | **Command Center** → click example card | Steps list displayed |

---

## 21. UI navigation map

| UI tab | Requirements covered (primary) |
|--------|-------------------------------|
| **Command Center** | R-196, stats, examples |
| **Examination Lab** | R-001–004, R-040, R-050–052, R-090, R-150–167 (filters) |
| **Live Capture** | R-180–183 |
| **Markup Studio** | R-082–085, R-163, R-170–171 |
| **Timeline Pro** | R-070–075, R-112–113, R-174–175 |
| **Forensic Tools** | R-075, R-074, R-121, R-122–124, R-130–134, R-140–142, R-160–165, R-172–173, R-195 |
| **Chain of Custody** | R-143 |
| **Legal Export** | R-030–038, R-110 |
| **Case Reports** | R-130–132 |

---

## 22. Automated smoke script (optional)

Run from project root (API must be running):

```bash
chmod +x scripts/run-requirements-smoke.sh

# Core API only (no test files)
./scripts/run-requirements-smoke.sh

# Full API coverage (recommended)
SAMPLE_IMAGE=~/Desktop/sample.jpg \
SAMPLE_VIDEO=~/Desktop/sample.mp4 \
SAMPLE_SRT=~/Desktop/sample.srt \
SAMPLE_VIDEO_B=~/Desktop/sample-b.mp4 \
./scripts/run-requirements-smoke.sh
```

**Printable checklist:** [`docs/REQUIREMENTS-TEST-CHECKLIST.md`](REQUIREMENTS-TEST-CHECKLIST.md) — checkboxes for all 104 requirements (print or Save as PDF).

Legacy one-liner:

```bash
BASE=http://127.0.0.1:9450
curl -sf "$BASE/api/health" | grep -q '"status":"ok"' && echo "health OK"
curl -sf "$BASE/api/filters" | grep -q '"count"' && echo "filters OK"
curl -sf "$BASE/api/license/status" | grep -q 'machine_id' && echo "license OK"
curl -sf "$BASE/api/forensics/cases/active" | grep -q 'case_id' && echo "case OK"
echo "Smoke complete"
```

---

## 23. Sign-off checklist

| Milestone | Action |
|-----------|--------|
| **Release candidate** | All **IMPLEMENTED** rows tested once |
| **Partial acceptance** | Each **PARTIAL** row: test what exists + document gap |
| **Planned** | No tracked planned rows remain; test all implemented rows before sign-off |
| **Evidence bundle** | Screenshots + API JSON + output files per section |

---

## 24. Document maintenance

| Event | Update |
|-------|--------|
| New phase shipped | Add rows / change status in this doc + `REQUIREMENTS-COMPLIANCE.md` |
| New API route | Add curl example under matching requirement ID |
| UI tab renamed | Update Section 21 map |

**Prepared by:** Mohit M  
**Next review:** Each release tag
