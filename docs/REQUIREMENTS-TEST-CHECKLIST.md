# Chakshu — Requirements Test Checklist (Printable)

**Product:** Chakshu (AI-IVE) v1.0.0  
**Tester:** ______________________ **Date:** __________  
**Build / commit:** ______________________ **Platform:** __________  

**Instructions:** Check each box when pass criteria in [`REQUIREMENTS-TEST-GUIDE.md`](REQUIREMENTS-TEST-GUIDE.md) are met.  
**Automated API smoke:** `./scripts/run-requirements-smoke.sh`  
**Legend:** ☐ = not tested · ☑ = pass · ⊘ = N/A (PLANNED)

---

## Prerequisites

| ☐ | Item |
|---|------|
| ☐ | API running — http://127.0.0.1:9450/api/health → `opencv: true`, `ffmpeg: true` |
| ☐ | UI running — http://127.0.0.1:9451 |
| ☐ | Test files ready: sample.jpg, sample.mp4, sample.srt, second video (optional) |
| ☐ | Smoke script run: `SAMPLE_IMAGE=... SAMPLE_VIDEO=... ./scripts/run-requirements-smoke.sh` |

---

## Section 1 — Core Platform

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-001 | ☐ | ≥140 filters | Examination Lab filter count / `GET /api/filters` |
| R-002 | ☐ | Standalone operation | Local API+UI without cloud |
| R-003 | ☐ | License protection | `GET /api/license/status` |
| R-004 | ☐ | Visible filter execution | Apply Brightness → preview changes |

## Section 2 — Video Decoding

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-010 | ☐ | FFmpeg decoding | Load sample.mp4 |
| R-011 | ☐ | DirectShow (PARTIAL) | Windows only / FFmpeg fallback |
| R-012 | ☐ | VfW (PARTIAL) | Windows adapter / fallback |
| R-013 | ☐ | QuickTime (PARTIAL) | Load .mov if available |
| R-014 | ☐ | Formats + codecs | Settings media compatibility + Legal Export |

## Section 3 — Bookmarks & Projects

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-020 | ☐ | Bookmarks | `POST /api/bookmarks` |
| R-021 | ☐ | Project YAML | `GET /api/project/current` |
| R-022 | ☐ | Import projects | Settings import inspect/import |

## Section 4 — Export

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-030 | ☐ | Stream copy export | `POST /api/export` copy mode |
| R-031 | ☐ | CFR export | CFR + fps in export |
| R-032 | ☐ | VFR export | VFR mode |
| R-033 | ☐ | Batch conversion | batch/queue module |
| R-034 | ☐ | Frames to PDF | Legal Export → PDF |
| R-035 | ☐ | Media bundle | `POST /api/export/media-bundle` |
| R-036 | ☐ | I-frame export | Legal Export → I-frames |
| R-037 | ☐ | Trim no transcode | Forensic Tools trim |
| R-038 | ☐ | Frame list export | export-frames API |

## Section 5 — Images

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-040 | ☐ | JPEG/PNG/TIFF/BMP | Ingest each format |
| R-041 | ☐ | RAW / specialized formats | Settings compatibility + .dng with rawpy |
| R-042 | ☐ | Nested folders | scan_folder |

## Section 6 — Editing

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-050 | ☐ | Undo / Redo | Apply filter → Undo |
| R-051 | ☐ | Multi-video (PARTIAL) | timeline/secondary API |
| R-052 | ☐ | Non-destructive master | Reset to Original |

## Section 7 — GPU

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-060 | ☐ | GPU encode | `GET /api/gpu/encoders` |

## Section 8 — Stream Analysis

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-070 | ☐ | Timestamp extraction | Timeline Pro build |
| R-071 | ☐ | Demultiplexing | analyze-video streams |
| R-072 | ☐ | I/P/B visibility | Stream Analysis panel |
| R-073 | ☐ | Per-frame metadata | Timeline frame click |
| R-074 | ☐ | MPEG macroblocks (PARTIAL) | Macroblock Overlay |
| R-075 | ☐ | Advanced seek | Seek Time / I-Frame |

## Section 9 — Tracking & Annotations

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-080 | ☐ | Tracking (PARTIAL) | tracker module |
| R-081 | ☐ | Reuse tracking data | JSON save/load |
| R-082 | ☐ | Markup tools (6) | Markup Studio toolbar |
| R-083 | ☐ | Annotations + burn | Arrow → Apply to Frame |
| R-084 | ☐ | Grouped annotations | Group ID field |
| R-085 | ☐ | Snap / guides | Snap 10px checkbox |

## Section 10 — AI / ML

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-090 | ☐ | AI enhance (PARTIAL) | both_enhance_ai filter |
| R-091 | ☐ | ONNX import | AIModelRegistry |

## Section 11 — i18n & Accessibility

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-100 | ☐ | Multilingual (PARTIAL) | `GET /api/i18n/es` |
| R-101 | ☐ | Accessibility (PARTIAL) | theme.py palettes |

## Section 12 — Audio

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-110 | ☐ | Audio extraction | Legal Export audio |
| R-111 | ☐ | Volume/mute | Shared Evidence Path + Timeline audio |
| R-112 | ☐ | Frame audio (PARTIAL) | Timeline + video |
| R-113 | ☐ | Multichannel | Probe audio channels |
| R-114 | ☐ | Audio redaction | audio/redact API |
| R-115 | ☐ | Add audio stream | audio/mux API |
| R-116 | ☐ | A/V sync adjust | audio/sync API |
| R-117 | ☐ | Pad video to audio | mux pad API |

## Section 13 — Subtitles & Overlays

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-120 | ☐ | SRT/SMI parse | `POST /api/subtitles/parse` |
| R-121 | ☐ | Subtitle customization | Forensic Tools burn |
| R-122 | ☐ | Timestamp overlay | Timestamp + Grid |
| R-123 | ☐ | Grid overlay | Same |
| R-124 | ☐ | Side-by-side (PARTIAL) | Compare session |
| R-125 | ☐ | PiP (PARTIAL) | overlay API |

## Section 14 — Reports

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-130 | ☐ | HTML/PDF/DOC reports | Case Reports |
| R-131 | ☐ | Paper sizes | A4/Letter/Legal/A3 |
| R-132 | ☐ | Templates | standard/detailed/… |
| R-133 | ☐ | Secure copy in reports | Secure Copy + Case Reports |
| R-134 | ☐ | Clipboard export | Copy Frame / Hashes |

## Section 15 — Forensic Integrity

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-140 | ☐ | Multi-algorithm hash | Hash Evidence File |
| R-141 | ☐ | Frame hash | hash/frame API |
| R-142 | ☐ | Secure copy + report | Secure Copy button |
| R-143 | ☐ | Chain of custody | Custody tab |
| R-144 | ☐ | Audit log | cases/{id}/audit |
| R-145 | ☐ | Secure media batch | Legal Export secure media batch |

## Section 16 — Advanced Processing

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-150 | ☐ | Deinterlace | adv_deinterlace / advanced/deinterlace |
| R-151 | ☐ | Lens distortion | geo_barrel |
| R-152 | ☐ | Panoramic (PARTIAL) | adv_panorama |
| R-153 | ☐ | Homomorphic | adv_homomorphic |
| R-154 | ☐ | Auto contrast + halo | adv_auto_contrast |
| R-155 | ☐ | Color separation | adv_color_separate |
| R-156 | ☐ | Motion deblur | adv_motion_deblur |
| R-157 | ☐ | Multi-image align | Geometry Correction multi-image alignment |
| R-158 | ☐ | Perspective stabilize (PARTIAL) | adv_perspective |
| R-159 | ☐ | Super-resolution | adv_super_resolution |
| R-160 | ☐ | Video stabilize | Forensic Tools Stabilize |
| R-161 | ☐ | Frame dup FPS | Adjust FPS |
| R-162 | ☐ | Manual FPS | Same |
| R-163 | ☐ | Privacy redaction | Markup Redact |
| R-164 | ☐ | Freeze frame | advanced/freeze |
| R-165 | ☐ | Reverse | Forensic Tools Reverse |
| R-166 | ☐ | JPEG artifact reduce | adv_jpeg_artifact |
| R-167 | ☐ | Channel invert/replace | adv_channel_replace |

## Section 17 — Measurement & Analysis

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-170 | ☐ | Image measurement | Markup Measure |
| R-171 | ☐ | Speed estimation | Measure + Δt |
| R-172 | ☐ | Stream sync | Find Stream Offset |
| R-173 | ☐ | Merge / concat | Merge A/V, Concat |
| R-174 | ☐ | VFR playback (PARTIAL) | VFR timeline flag |
| R-175 | ☐ | Region analysis | Timeline region panel |

## Section 18 — Capture

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-180 | ☐ | Live video capture | Live Capture webcam |
| R-181 | ☐ | Sequence → video | sequence to video |
| R-182 | ☐ | Real-time filters | MJPEG + filter_id |
| R-183 | ☐ | Screen capture | Screen capture button |

## Section 19 — Platform

| ID | ☐ | Requirement | UI / API shortcut |
|----|---|-------------|-------------------|
| R-190 | ☐ | Windows x64 install | build_x64.ps1 |
| R-191 | ☐ | Windows x86 (PARTIAL) | build_x86.ps1 |
| R-192 | ☐ | Operation logging | logging/operations.py |
| R-193 | ☐ | VMS export (PARTIAL) | faststart MP4 in VLC |
| R-194 | ☐ | External metadata | metadata export |
| R-195 | ☐ | Persistent notes | Forensic Tools notes |
| R-196 | ☐ | Example workflows | Command Center examples |

---

## Sign-off summary

| Metric | Count |
|--------|-------|
| Total requirements | 104 |
| Tested (☑) | _____ |
| Failed | _____ |
| N/A (PLANNED) | 0 |
| Partial accepted with notes | _____ |

**Notes / blockers:**

_____________________________________________________________________________

_____________________________________________________________________________

**Approver:** ______________________ **Date:** __________

---

*Print this page or export to PDF: File → Print → Save as PDF.  
Detailed steps: `docs/REQUIREMENTS-TEST-GUIDE.md`*
