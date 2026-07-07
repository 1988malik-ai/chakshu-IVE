# Chakshu Forensics Compliance And Test Steps

This document maps the supplied requirement list to practical verification steps for Chakshu Forensics. It is intended for product acceptance testing, demo preparation, and release sign-off.

Related references:

- `docs/REQUIREMENTS-COMPLIANCE.md` — detailed requirement matrix.
- `docs/REQUIREMENTS-TEST-GUIDE.md` — requirement-by-requirement guide.
- `docs/WORKFLOW-TEST-GUIDE.md` — end-to-end examiner workflows.

## Test Setup

1. Start the backend and frontend.

   ```bash
   source .venv/bin/activate
   export PYTHONPATH=src
   python -m aive.api.server
   ```

   In another terminal:

   ```bash
   cd frontend
   npm run dev
   ```

2. Open `http://localhost:9451`.
3. Create/set a Case ID from the top bar.
4. Prepare test files:
   - One JPEG or PNG image.
   - One MP4 video with audio.
   - Optional VFR phone/screen-recorded clip.
   - Optional SRT subtitle file.

## High-Priority Compliance Checklist

| Requirement | Status | Evidence | Test Steps | Pass Criteria |
|---|---:|---|---|---|
| At least 140 image/video filters | Implemented | `src/aive/filters/catalog.py` asserts `len(FILTER_CATALOG) >= 140`; architecture notes show 191 registered filters | Open Examination Lab and inspect filter list; or call `GET /api/filters` | Filter count is at least 140 and image/video/both filters are scoped correctly |
| Standalone system with license protection | Implemented | `src/aive/license/protection.py`, `scripts/generate_license.py`, `docs/LICENSE-AND-ACTIVATION.md` | Run license generator help and license status flow | App has trial/license validation path and activation docs |
| Major video codec decoding | Implemented | FFmpeg/OpenCV loaders in `src/aive/media/`, `src/aive/video/` | Ingest common MP4/MOV/AVI where supported by local FFmpeg/OpenCV | Video preview loads and timeline metadata appears |
| Bookmark frames and filters with metadata | Implemented | `frontend/src/components/BookmarksPanel.jsx`, API bookmark routes | Apply a filter, fill label/notes/tags, click Bookmark this frame/current filter | Bookmark appears with metadata and Go to/Edit/Delete works |
| Original and processed media export | Implemented | `src/aive/export/media_bundle.py`, Legal Export UI | Legal Export -> Export examination bundle | Original and processed outputs are written to configured folders |
| CFR and VFR video export | Implemented | `src/aive/export/exporter.py`, `tests/test_video_export_framerate.py` | Legal Export -> Frame rate mode: CFR, export; repeat with VFR | CFR command uses fixed FPS; VFR command preserves variable timing mode |
| Stream copy / minimal transcoding | Implemented | `ExportOptions.use_stream_copy`, `VideoExporter.build_command` | Set video codec to Stream copy and export a compatible video | ffmpeg command uses `-c:v copy` when no filters require re-encode |
| GPU-accelerated H.264/H.265 encoding | Implemented where hardware supports it | `src/aive/gpu/encode.py`, Legal Export codec Auto GPU | Legal Export -> video codec Auto GPU, export video | Available GPU encoder is selected, otherwise CPU fallback works |
| I/P/B frame visibility | Implemented | Timeline Pro and stream analysis endpoints | Load video -> Timeline Pro / Stream Analysis -> Analyze I/P/B frames | Frame type summary/table appears |
| Timestamp-based playback speed control | Implemented | `ForensicVideoTransport.jsx`, `TimelineProPage.jsx` | Timeline Pro -> choose 0.25x, 1x, 2x, 4x; play | Timecode advances at selected speed and frame preview updates |
| Variable frame rate playback via timestamps | Partial/Implemented for PTS seek | `src/aive/video/timeline.py`, VFR detection chips | Load VFR clip -> Timeline Pro | Timeline flags VFR and seeking uses timestamp/PTS metadata |
| Subtitle rendering SRT/SMI | Implemented | `src/aive/subtitles/`, Subtitle panel | Upload SRT, preview subtitles, burn/export | Subtitle text renders at expected timestamps |
| PDF frame export with layout settings | Implemented | `src/aive/export/pdf_frames.py`, Legal Export PDF panel | Set page size/orientation/rows/columns; export PDF | PDF generated with selected layout |
| Audio extraction/playback/mute/volume | Implemented | Audio panels and `src/aive/audio/` | Load video -> use audio player, volume, mute, extract audio | Playback controls work and audio extract file is created |
| Audio redaction | Implemented | `src/aive/audio/redaction.py`, Audio Redaction panel | Add mute region and export redacted audio/video | Output has selected region muted |
| Add/mux audio stream | Implemented | `src/aive/audio/mux.py` | Forensic Tools -> audio mux panel | Output video includes selected/new audio stream |
| A/V sync adjustment | Implemented | Audio sync tools | Use A/V offset control on loaded media | Offset is applied/export command succeeds |
| Video overlays and side-by-side comparison | Implemented | `VideoOverlayComparePanel.jsx`, compare library | Examination Lab -> Video Tools -> compare/overlay | Side-by-side/PiP overlay previews and exports |
| PiP display | Implemented | Video overlay compare settings | Enable PiP mode and choose position | PiP appears in selected position |
| Geometric distortion/perspective correction | Implemented | `PerspectiveCorrectionPanel.jsx`, `geo_keystone`, `both_perspective_match` | Geometry Correction -> Perspective correction -> drag corners -> Preview/Apply | Corrected preview appears; Apply updates frame; Revert correction restores |
| Panoramic conversion | Implemented | `PanoramaConversionPanel.jsx`, `adv_omni_panorama` | Geometry Correction -> Omnidirectional -> Panorama | Preview/apply produces flattened panorama/perspective view |
| Illumination correction algorithms | Implemented | `src/aive/filters/illumination.py`, filters `ill_homomorphic`, `ill_retinex`, `ill_adaptive_flatten` | Search illumination filters, apply each to image/video frame | Uneven lighting changes and pipeline records filter |
| Contrast/brightness auto adjustment | Implemented | Filter catalog and forensic ops | Apply Auto Contrast / Auto Levels / Brightness | Preview changes and can reset to original |
| Color/component separation | Implemented | Filter catalog `adv_color_separate`, channel tools | Apply color separation/channel filters | Output isolates or adjusts target channel |
| Hash verification, multi-algorithm | Implemented | `src/aive/forensics/hash_verify.py` | Forensic Tools -> Hash Evidence File | MD5, SHA-1, SHA-256, SHA-512 appear |
| Frame-level hash verification | Implemented | capabilities hash frame endpoint | Load frame -> hash current frame | Frame hash is returned |
| Super-resolution from video frames | Implemented | `routes_ai.py` maps video super-resolution to `both_upscale_ai` | Load video, seek/load frame, Forensic Tools -> AI/ML Enhancement -> Super Resolution -> Apply to Frame | Examination Lab preview updates and pipeline includes upscale |
| Object tracking and stabilization | Implemented | `TrackingStabilizePanel.jsx`, `src/aive/video/tracking_stabilize.py` | Video Tools -> Object-tracking stabilization -> draw box -> Track -> Export stabilized video | Tracking completes and export unlocks |
| Privacy redaction via blur/pixelation | Implemented | Markup/redaction tools and filters | Markup Studio / filters -> redact/pixelate region | Redacted output is visible and exportable |
| Annotation tools with snapping/guides | Implemented | `ExamCanvas.jsx`, Markup Studio | Draw arrow/text/rectangle/measurement with snap enabled | Annotation appears at cursor, can apply to frame |
| Measurement tools with error estimates | Implemented | `src/aive/measurement/tools.py`, `tests/test_measurement_tools.py` | Markup Studio -> Measure -> set unit/calibration/error fields -> draw line | Distance shown with `±` uncertainty and selected unit |
| Object speed with uncertainty | Implemented | `estimate_speed` in measurement tools | Use measurement with delta time/speed fields where available | Speed includes uncertainty propagation |
| Secure copy with hash report | Implemented | secure copy capability | Forensic Tools -> Secure Copy + Report | Copied file and JSON/hash report created |
| Secure media direct loading and batch export | Implemented | `secure_media_batch.py`, Legal Export secure media panel | Legal Export -> Secure media folder -> Scan -> Load into case -> Batch export | Folder scan, referenced load, and verified batch export complete |
| Timestamp editing and region analysis | Implemented | `TimestampEditorPanel.jsx`, `RegionAnalysisPanel.jsx` | Timeline/Tools -> edit timestamp overlay; run region I/P/B analysis | Timestamp overlay applies; region table shows frame distribution |
| JPEG artifact reduction / denoise / sharpen | Implemented | filter catalog restore/noise/sharpen categories | Apply JPEG Artifact Reduction, Denoise, Sharpen | Output changes and filter is recorded |
| Live capture and screen capture | Implemented | `LiveCapture.jsx`, capture APIs | Live Capture -> Start Webcam / Record 5s Screen / Build Video | Capture preview appears or output video is created |
| Image sequence to video | Implemented | `src/aive/capture/sequence_video.py` | Live Capture -> set frame folder -> Build Video | MP4 created from image sequence |
| Advanced seek by frame/time/I-frame | Implemented | Timeline Pro, `video/seek.py`, i-frame export | Timeline Pro -> seek by time/frame, export I-frames | Preview jumps accurately; I-frame folder generated |
| Notes linked to project | Implemented | `ProjectNotesPanel.jsx`, project notes API | Open Notes -> add note linked to evidence | Note persists for current project |
| Automated reports HTML/PDF/DOCX | Implemented | `CaseReportsPanel.jsx`, report API | Case Reports -> choose formats -> Generate | HTML/PDF/DOCX outputs are saved to reports folder |
| Report paper sizes/templates/settings | Implemented | Case Reports panel | Change template, paper size, orientation, title, author | Output uses selected metadata/layout |
| Localization and accessibility | Implemented | Locale and settings panels | Settings -> language/accessibility options | UI language/accessibility options apply |
| Windows compatibility / packaging | Implemented/packaging dependent | `desktop/`, `packaging/`, Windows docs | Follow `docs/WINDOWS-INSTALL.md` or packaged build workflow | Windows app/backend starts on supported target |

## End-To-End Acceptance Runs

### Run 1: Image Examination

1. Set Case ID.
2. Ingest a JPEG/PNG.
3. Apply at least three filters: illumination correction, contrast/brightness, and JPEG artifact/noise/sharpen.
4. Open Geometry Correction and apply Perspective correction.
5. Open Markup Studio; add arrow, text, rectangle, and one measurement with unit/error fields.
6. Bookmark the frame and current filter with label, notes, tags, priority, examiner.
7. Export PDF frames and generate a case report.

Pass criteria: processed preview updates, filters are visible in pipeline, measurement includes uncertainty, bookmark is saved, PDF/report files are created.

### Run 2: Video Examination

1. Ingest an MP4 video.
2. Timeline Pro: play at 0.25x, 1x, 2x, and 4x.
3. Seek by timestamp and load a frame.
4. Analyze frame types and region I/P/B distribution.
5. Apply super-resolution to the loaded video frame.
6. Use Video Tools for side-by-side overlay/PiP and object-tracking stabilization.
7. Export I-frames and a processed media bundle.

Pass criteria: playback controls update timecode/frame preview, I/P/B analysis returns data, super-resolution updates Examination Lab, tracking export completes, exported files exist.

### Run 3: Export And Chain Of Custody

1. Legal Export: configure project root and use case subfolder.
2. Export media bundle as CFR with selected FPS.
3. Export media bundle as VFR.
4. Secure media: scan a folder, load references into case, batch export.
5. Open Chain of Custody and Case Reports.

Pass criteria: CFR/VFR exports are created, secure media report is created, custody log records ingest/enhancement/export actions, case report output directory is a valid path.

## Technical Smoke Commands

Filter count:

```bash
PYTHONPATH=src .venv/bin/python -c "from aive.filters.catalog import FILTER_CATALOG; print(len(FILTER_CATALOG)); assert len(FILTER_CATALOG) >= 140"
```

CFR/VFR exporter command behavior:

```bash
PYTHONPATH=src .venv/bin/python -c "from pathlib import Path; from aive.export.exporter import ExportOptions, FrameRateMode, VideoExporter; e=VideoExporter(ffmpeg='ffmpeg'); print(e.build_command(Path('in.mp4'), ExportOptions(output_path=Path('cfr.mp4'), use_stream_copy=False, frame_rate_mode=FrameRateMode.CFR, fps=25.0))); print(e.build_command(Path('in.mp4'), ExportOptions(output_path=Path('vfr.mp4'), use_stream_copy=False, frame_rate_mode=FrameRateMode.VFR, fps=25.0)))"
```

Focused tests, when `pytest` is installed:

```bash
PYTHONPATH=src pytest tests/test_illumination_filters.py tests/test_measurement_tools.py tests/test_video_export_framerate.py tests/test_secure_media_batch.py -q
```

Frontend build:

```bash
cd frontend
npm run build
```

## Known Validation Notes

- Some codec support depends on the installed FFmpeg/OpenCV build and OS codecs.
- GPU encoding depends on local hardware and installed encoder support.
- VFR preservation should be verified with a VFR sample and `ffprobe` where available.
- 32-bit Windows support is packaging-dependent and should be tested with a dedicated build artifact.
- Multi-image perspective alignment and advanced tracking behavior should be validated with representative real evidence, not only synthetic files.
