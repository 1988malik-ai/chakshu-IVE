# Chakshu Requirements Compliance Matrix

**Document:** Requirements Traceability & Compliance  
**Author:** Mohit M  
**Product:** Chakshu — Digital Media Examination Platform  
**Version:** 1.0.0  
**Date:** 2026-05-29  
**Classification:** Internal / Procurement Support  

**Test guide:** See [`docs/REQUIREMENTS-TEST-GUIDE.md`](REQUIREMENTS-TEST-GUIDE.md) for step-by-step verification of each requirement ID.  
**Workflow testing:** [`docs/WORKFLOW-TEST-GUIDE.md`](WORKFLOW-TEST-GUIDE.md) — end-to-end examiner scenarios (WF-01 … WF-12).  
**Printable checklist:** [`docs/REQUIREMENTS-TEST-CHECKLIST.md`](REQUIREMENTS-TEST-CHECKLIST.md) · **Smoke script:** `scripts/run-requirements-smoke.sh`

---

## Legend

| Status | Meaning |
|--------|---------|
| **IMPLEMENTED** | Delivered and verifiable in current build |
| **PARTIAL** | Foundation exists; limited scope or needs hardening |
| **PLANNED** | Designed in architecture; not yet complete |
| **NOT STARTED** | Not yet in codebase |

| Priority | Source |
|----------|--------|
| **MUST** | Mandatory requirement |
| **SHOULD** | Recommended / optional enhancement |

---

## 1. Core Platform

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-001 | ≥140 image and video processing filters | MUST | **IMPLEMENTED** | `src/aive/filters/catalog.py` — 191 filters registered |
| R-002 | Standalone system operation | MUST | **IMPLEMENTED** | Desktop: Electron + API; `scripts/setup-and-run.sh`, `START.command` |
| R-003 | License protection | MUST | **IMPLEMENTED** | `src/aive/license/protection.py` — hardware-bound keys, trial |
| R-004 | Filter processing execution (visible enhancement) | MUST | **IMPLEMENTED** | `filters/forensic_ops.py` — 191 live catalog filters; `engine.is_implemented()` |

---

## 2. Video Decoding

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-010 | FFmpeg decoding | MUST | **IMPLEMENTED** | `src/aive/codecs/decoders.py` — `FFmpegDecoder` |
| R-011 | DirectShow (Windows) | MUST | **PARTIAL** | `DirectShowDecoder` adapter + FFmpeg fallback |
| R-012 | Video for Windows (VfW) | MUST | **PARTIAL** | `VideoForWindowsDecoder` adapter |
| R-013 | QuickTime (optional) | MUST | **PARTIAL** | `QuickTimeDecoder` adapter |
| R-014 | Standard formats + system codec extension | MUST | **PARTIAL** | `export/exporter.py` presets; FFmpeg-dependent |

---

## 3. Bookmarks & Project Documentation

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-020 | Bookmark frames/filters with custom metadata | MUST | **IMPLEMENTED** | `src/aive/bookmarks/store.py`, API `/api/bookmarks` |
| R-021 | Human-readable project format | MUST | **IMPLEMENTED** | `src/aive/project/workflow.py` — `.aive.yaml` |
| R-022 | Import projects from compatible tools | SHOULD | **PARTIAL** | JSON/YAML import in `workflow.py` |

---

## 4. Export — Video & Media

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-030 | Wide format export; minimal transcoding when possible | MUST | **IMPLEMENTED** | `export/exporter.py` — `use_stream_copy` |
| R-031 | CFR export | MUST | **IMPLEMENTED** | `FrameRateMode.CFR` |
| R-032 | VFR export | MUST | **IMPLEMENTED** | `FrameRateMode.VFR`, `-vsync vfr` |
| R-033 | Batch conversion multi-file/folder | MUST | **IMPLEMENTED** | `src/aive/batch/queue.py` |
| R-034 | Export frames to PDF + layout settings | MUST | **IMPLEMENTED** | `export/pdf_frames.py`, API `/api/export/pdf-frames` |
| R-035 | Export original + processed + encoding settings | MUST | **IMPLEMENTED** | `export/media_bundle.py` |
| R-036 | Selective I-frame export | MUST | **IMPLEMENTED** | `export/i_frames.py` |
| R-037 | Frame trim/selection without transcoding | MUST | **IMPLEMENTED** | `export/trim.py`, `/api/capabilities/video/trim` |
| R-038 | User-defined frame list selection | MUST | **IMPLEMENTED** | `export/trim.py` `export_frame_list_copy`, `/api/capabilities/video/export-frames` |

---

## 5. Images & File Organization

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-040 | JPEG, PNG, TIFF, BMP | MUST | **IMPLEMENTED** | `media/loader.py` |
| R-041 | RAW / specialized formats | MUST | **PARTIAL** | RAW via optional `rawpy`; loader hooks |
| R-042 | Nested folder organization | MUST | **IMPLEMENTED** | `MediaLibrary.scan_folder()` |

---

## 6. Editing & Multi-Media

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-050 | Undo / Redo | MUST | **IMPLEMENTED** | `undo/stack.py`, API `/api/edit/undo|redo` |
| R-051 | Simultaneous multi-video load | MUST | **PARTIAL** | `/api/timeline/video/secondary`, config `max_simultaneous_videos` |
| R-052 | Non-destructive master frame (forensic) | MUST* | **IMPLEMENTED** | `session.master_frame` + pipeline re-render |

*Forensic architecture extension beyond original RFP wording.

---

## 7. GPU Encoding

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-060 | GPU H.264 / H.265 (CUDA, Quick Sync) | MUST | **IMPLEMENTED** | `gpu/encode.py` — NVENC, QSV, AMF detection |

---

## 8. Stream Analysis & Frame Types

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-070 | Timestamp extraction | MUST | **IMPLEMENTED** | `analysis/stream.py` — `extract_timestamps()` |
| R-071 | Demultiplexing | MUST | **IMPLEMENTED** | `StreamAnalyzer.demux_stream()` |
| R-072 | I / P / B frame visibility | MUST | **IMPLEMENTED** | `frame_type_summary()`, forensics UI |
| R-073 | Per-frame metadata analysis/filtering | MUST | **IMPLEMENTED** | `analysis/frame_metadata.py`, `/api/timeline/*` |
| R-074 | MPEG macroblocks / motion vectors | MUST | **PARTIAL** | `analysis/mpeg_viz.py`, `/api/capabilities/mpeg/visualize` |
| R-075 | Advanced seek (frames, time, I-frames) | MUST | **IMPLEMENTED** | `video/seek.py`, capabilities API + Forensic Tools UI |

---

## 9. Object Tracking & Annotations

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-080 | Manual / automatic / keyframe tracking | MUST | **PARTIAL** | `tracking/tracker.py` — OpenCV CSRT/KCF |
| R-081 | Reuse tracking data | MUST | **IMPLEMENTED** | JSON save/load on `ObjectTracker` |
| R-082 | Multiple tracking/selection tools | MUST | **IMPLEMENTED** | Markup Studio — 6 tools in `ExamCanvas.jsx` |
| R-083 | Annotations (arrows, text, shapes) + tracking | MUST | **IMPLEMENTED** | `annotations/store.py`, `/api/markup/*` |
| R-084 | Grouped annotations | MUST | **IMPLEMENTED** | `group_id` on annotations |
| R-085 | Alignment aids (snapping, guides) | MUST | **IMPLEMENTED** | `annotations/snap.py`, snap grid in UI |

---

## 10. AI / ML

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-090 | AI-based enhancement | SHOULD | **IMPLEMENTED** | `ai/enhance.py` builtins + `POST /api/ai/enhance/session`, Forensic Tools UI |
| R-091 | Custom model import (ONNX) | SHOULD | **IMPLEMENTED** | `ai/models.py`, `POST /api/ai/models/import`, `models/README.md` |

---

## 11. Localization & Accessibility

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-100 | Multilingual UI + reports | SHOULD | **IMPLEMENTED** | `i18n/forensic_strings.py` — EN, HI, MR, GU (Indian context) |
| R-101 | Vision / color-blind accessibility | SHOULD | **IMPLEMENTED** | `accessibility/theme.py`, `styles/a11y.css`, Settings sidebar + `/api/accessibility/*` |

---

## 12. Audio

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-110 | Audio stream extraction | MUST | **IMPLEMENTED** | `export/audio.py` |
| R-111 | Playback volume / mute | MUST | **PARTIAL** | `frontend/components/AudioPlayer.jsx` |
| R-112 | Frame-by-frame audio playback | MUST | **PARTIAL** | Timeline synced `<video>` + `audio/player.py` sync map |
| R-113 | Multichannel audio | MUST | **IMPLEMENTED** | `audio/player.py`, `/api/timeline/audio/channels` |
| R-114 | Audio redaction | MUST | **IMPLEMENTED** | `audio/redaction.py`, `/api/capabilities/audio/redact` |
| R-115 | Add new audio streams | MUST | **IMPLEMENTED** | `audio/mux.py`, `/api/capabilities/audio/mux` |
| R-116 | A/V sync adjustment | MUST | **IMPLEMENTED** | `audio/mux.py` `adjust_av_sync` |
| R-117 | Duration mismatch → pad video | MUST | **IMPLEMENTED** | `audio/mux.py` `pad_video_to_audio_length` |

---

## 13. Subtitles & Overlays

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-120 | SRT / SMI rendering | MUST | **IMPLEMENTED** | `subtitles/renderer.py`, `/api/capabilities/subtitles/*`, Forensic Tools **Subtitles** panel |
| R-121 | Subtitle overlay customization | MUST | **IMPLEMENTED** | `/api/capabilities/subtitles/burn` + force_style |
| R-122 | Timestamp overlay + formatting | MUST | **IMPLEMENTED** | `overlays/compose.py`, overlay API |
| R-123 | Grid overlay | MUST | **IMPLEMENTED** | `overlays/compose.py` `draw_grid` |
| R-124 | Video overlays / side-by-side | MUST | **IMPLEMENTED** | `comparison/session.py`, compare API, JPEG export, `tests/test_compare_overlays.py` |
| R-125 | Picture-in-Picture | MUST | **IMPLEMENTED** | `overlays/compose.py` `draw_pip`, Examination Lab PiP workflow, `tests/test_compare_overlays.py` |

---

## 14. Reports & Compliance Outputs

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-130 | Automated reports HTML/PDF/DOC | MUST | **IMPLEMENTED** | `reports/generator.py` |
| R-131 | Various paper sizes | MUST | **IMPLEMENTED** | A4, Letter, Legal, A3 |
| R-132 | Customizable templates | MUST | **IMPLEMENTED** | standard, detailed, executive, minimal |
| R-133 | Secure copy in reports | MUST | **PARTIAL** | `forensics/secure_copy.py`, `/api/capabilities/copy/secure` |
| R-134 | Export to office / clipboard | MUST | **IMPLEMENTED** | `/api/capabilities/clipboard/frame`, Forensic Tools copy |

---

## 15. Forensic Integrity & Chain of Custody

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-140 | File hash (multiple algorithms) | MUST | **IMPLEMENTED** | `forensics/hash_verify.py` — MD5, SHA-1, SHA-256, SHA-512 |
| R-141 | Frame-level hash verification | MUST | **IMPLEMENTED** | `hash_frame()`, `/api/capabilities/hash/frame` |
| R-142 | Secure copy + hash validation report | MUST | **IMPLEMENTED** | `forensics/secure_copy.py` |
| R-143 | Chain of custody log | MUST* | **IMPLEMENTED** | `forensics/case.py`, UI Custody tab |
| R-144 | Audit log | MUST* | **IMPLEMENTED** | `forensics/audit.py` |
| R-145 | Direct load from secure media + batch export | MUST | **IMPLEMENTED** | `forensics/secure_media_batch.py`, `/api/forensics/secure-media/*`, Export tab UI |

*Forensic examination requirements.

---

## 16. Advanced Video / Image Processing

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-150 | Interlaced conversion | MUST | **IMPLEMENTED** | `filters/advanced.py` deinterlace + `video/advanced.py` yadif |
| R-151 | Geometric distortion correction | MUST | **IMPLEMENTED** | `lens_distortion_correct`, enhanced `geo_*` / `both_lens_correction` |
| R-152 | Panoramic / omnidirectional | MUST | **IMPLEMENTED** | `src/aive/panorama.py`, `PanoramaConversionPanel.jsx`, `tests/test_panorama_conversion.py` |
| R-153 | Homomorphic / illumination filters | MUST | **IMPLEMENTED** | `adv_homomorphic`, high-strength `clr_dehaze` |
| R-154 | Auto contrast/brightness + halo suppression | MUST | **IMPLEMENTED** | `adv_auto_contrast`, `both_auto_contrast` |
| R-155 | Color separation / component isolation | MUST | **IMPLEMENTED** | `adv_color_separate`, `clr_channel_mixer` |
| R-156 | Motion blur / defocus deblur | MUST | **IMPLEMENTED** | `adv_motion_deblur`, `both_deblur_ai` |
| R-157 | Multi-image perspective alignment | MUST | **PLANNED** | Requires multi-image input pipeline |
| R-158 | Perspective stabilization | MUST | **PARTIAL** | Frame preview + `/api/capabilities/advanced/perspective-stabilize` |
| R-159 | Super-resolution from video | MUST | **IMPLEMENTED** | `adv_super_resolution`, `rst_super_resolution` |
| R-160 | Video stabilization (auto + tracking-based) | MUST | **IMPLEMENTED** | `/api/capabilities/advanced/stabilize` (vidstab/deshake) |
| R-161 | Frame dup/removal for FPS adjust | MUST | **IMPLEMENTED** | `/api/capabilities/advanced/fps-adjust` |
| R-162 | Manual frame rate adjustment | MUST | **IMPLEMENTED** | Same FPS adjust API with `target_fps` |
| R-163 | Privacy redaction (pixelate/blur) | MUST | **IMPLEMENTED** | Markup Studio redact tool + `redaction/privacy.py` |
| R-164 | Frame freezing / placeholder video | MUST | **IMPLEMENTED** | `/api/capabilities/advanced/freeze` |
| R-165 | Reverse playback | MUST | **IMPLEMENTED** | `/api/capabilities/advanced/reverse` |
| R-166 | JPEG artifact reduction | MUST | **IMPLEMENTED** | `adv_jpeg_artifact`, `rst_jpeg_artifact` |
| R-167 | Channel invert/replace | MUST | **IMPLEMENTED** | `adv_channel_replace`, per-channel `clr_invert` |

---

## 17. Measurement & Analysis Tools

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-170 | Image measurement + error estimates | MUST | **IMPLEMENTED** | `measurement/tools.py`, `/api/capabilities/measure/distance` |
| R-171 | Object speed estimation | MUST | **IMPLEMENTED** | Markup measure + Δt; `measurement/tools.py` |
| R-172 | Stream sync / similarity | MUST | **IMPLEMENTED** | `analysis/sync.py`, `/api/capabilities/sync/similarity` |
| R-173 | Merge A/V streams; multi-video sequencing | MUST | **IMPLEMENTED** | `video/merge.py`, merge API + Forensic Tools UI |
| R-174 | VFR playback via timestamps | MUST | **PARTIAL** | `video/timeline.py` VFR detect; seek uses PTS |
| R-175 | Timestamp editing / region analysis | MUST | **IMPLEMENTED** | `region_summary`, Timeline region panel |

---

## 18. Capture & Real-Time

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-180 | Live video capture | MUST | **IMPLEMENTED** | `capture/realtime.py`, `LiveCapture.jsx`, `/api/capture/*` |
| R-181 | Image sequences as video | MUST | **IMPLEMENTED** | `capture/sequence_video.py` |
| R-182 | Real-time stream processing | MUST | **IMPLEMENTED** | MJPEG stream + live `filter_id` |
| R-183 | Screen capture (uncompressed) | MUST | **IMPLEMENTED** | `capture/screen.py` via FFmpeg |

---

## 19. Platform, Logging, Integration

| ID | Requirement | Pri | Status | Evidence / Module |
|----|-------------|-----|--------|-------------------|
| R-190 | Windows 64-bit install | MUST | **IMPLEMENTED** | `build/windows/build_x64.ps1` |
| R-191 | Legacy 32-bit support | MUST | **PARTIAL** | `build_x86.ps1` profile |
| R-192 | Optional operation logging | MUST | **IMPLEMENTED** | `logging/operations.py` |
| R-193 | VMS-compatible export playback | MUST | **PARTIAL** | `faststart`, `yuv420p` in exporter |
| R-194 | External tool metadata integration | MUST | **IMPLEMENTED** | `integration/metadata.py` — FFprobe/EXIF export |
| R-195 | Persistent notes panel | MUST | **IMPLEMENTED** | `project/examination_notes.py`, `ProjectNotesPanel.jsx`, `/api/project/notes`, saved in `.aive.yaml` |
| R-196 | Example projects / learning resources | MUST | **IMPLEMENTED** | `examples/workflows/`, Command Center UI |

---

## Summary Statistics

| Metric | Count | Notes |
|--------|-------|-------|
| **Total requirements** | 104 | All tracked in this matrix |
| **IMPLEMENTED** | 87 | 84% strict compliance |
| **PARTIAL** | 16 | 15% |
| **PLANNED** | 1 | 1% — multi-image align |
| **Progress score** | ~91% | Partial items counted at 50% |

| Status | MUST items (approx.) | Notes |
|--------|----------------------|-------|
| IMPLEMENTED | 80 | Markup, clipboard, subtitles, sync, merge, advanced video |
| PARTIAL | 22 | Multi-video, MPEG viz, subtitle customization polish |
| PLANNED | 2 | Multi-image perspective (R-157), secure media batch (R-145) |
| NOT STARTED | 0* | All items have architectural placement |

*All requirements are tracked; none are orphaned.

---

## Compliance Statement

Chakshu **meets or partially meets** the mandatory baseline for a **Version 1.0 forensic media examination platform**, with explicit gaps documented above. Full compliance with every MUST item requires phased delivery per **Architecture Roadmap** (`docs/ARCHITECTURE.md`).

**Prepared by:** Mohit M  
**Review cycle:** Update this matrix on each release tag.

---

## Recommended Phases (Mohit M)

| Phase | Focus | Target |
|-------|--------|--------|
| **1** | Forensic UI, custody, hash, I/P/B, PDF, reports | Done |
| **2** | Video timeline, advanced seek, frame-accurate audio | Done — `docs/PHASE-2.md` |
| **3** | Annotations, redaction, measurement | Done — `docs/PHASE-3.md` |
| **4** | Full filter implementation (140+ live) | Done — `docs/PHASE-4.md` |
| **5** | Capture, real-time, examples | Done — `docs/PHASE-5.md` |
| **6** | Advanced processing (Section 16) | Done — `docs/PHASE-6.md` |
| **7** | Markup fix, sync, merge, clipboard | Done — `docs/PHASE-7.md` |
| **8** | Localization (R-100) + accessibility (R-101) | Done — `docs/PHASE-8.md` |
| **9** | AI/ML enhancement + ONNX import (R-090, R-091) | Done — `docs/AI-ML-GUIDE.md` |
