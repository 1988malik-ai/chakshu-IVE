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

## Requirement-Level Verification Matrix

Use this table for release sign-off. Each row maps directly to `docs/REQUIREMENTS-COMPLIANCE.md`.

| ID | Acceptance Test Steps | Pass Criteria |
|---|---|---|
| R-001 | Start app, call `GET /api/filters`, or run the filter-count smoke command below. | At least 140 filters are returned; current catalog is 191. |
| R-002 | Start backend and frontend locally, then open `http://localhost:9451` without cloud services. | App opens and can ingest evidence in standalone mode. |
| R-003 | Run license generator help and check trial/license validation path. | License/trial status is available and hardware-bound validation code is present. |
| R-004 | Ingest image/video frame, apply several visible filters, then reset. | Preview changes, pipeline records filter, reset restores original. |
| R-010 | Ingest a common MP4/MOV file supported by local FFmpeg. | Video loads, first frame appears, duration/timeline metadata appears. |
| R-011 | On Windows, ingest a camera/DirectShow-compatible file or source; verify fallback. | Media opens via adapter or clear FFmpeg fallback. |
| R-012 | On Windows, ingest a legacy AVI/VfW sample. | File opens or compatibility limitation is reported clearly. |
| R-013 | Ingest a QuickTime/MOV sample. | MOV loads if local codecs/FFmpeg support it; failure gives clear message. |
| R-014 | Ingest/export several standard formats such as MP4, MOV, AVI, JPG, PNG, TIFF. | Supported formats load/export; unsupported codecs fail gracefully. |
| R-020 | Apply a filter, fill bookmark metadata, click frame and filter bookmark buttons. | Bookmark appears with label, notes, tags, priority, and can be edited/deleted. |
| R-021 | Save/export project YAML after ingest and filter operations. | `.aive.yaml` is human-readable and includes case/project data. |
| R-022 | Import a compatible JSON/YAML project file. | Project data loads or unsupported fields are reported cleanly. |
| R-030 | Legal Export: export a compatible video with stream copy enabled. | Output exists and command uses minimal transcoding where possible. |
| R-031 | Legal Export: select CFR mode and fixed FPS, then export. | Output exists and exporter command forces constant frame rate. |
| R-032 | Legal Export: select VFR mode, then export a VFR-capable clip. | Output exists and exporter preserves variable timing mode. |
| R-033 | Batch conversion: queue multiple files/folder and run. | Multiple outputs are created with per-file status. |
| R-034 | Legal Export: export selected frames to PDF with page/layout settings. | PDF exists and uses selected paper/orientation/layout. |
| R-035 | Legal Export: export media bundle with original and processed output enabled. | Bundle contains original, processed media, and settings metadata. |
| R-036 | Timeline/Export: export I-frames from a video. | I-frame files are written to output folder. |
| R-037 | Export a trimmed segment using start/end times without filters. | Trimmed output exists and uses copy path when compatible. |
| R-038 | Export a user-defined list of frame indices. | Requested frame images are written and named predictably. |
| R-040 | Ingest JPEG, PNG, TIFF, and BMP samples. | Each supported image opens and previews. |
| R-041 | Ingest RAW/specialized sample with optional dependencies installed. | Supported RAW opens; missing dependency is clearly reported. |
| R-042 | Scan/load evidence from nested folders. | Nested files are discovered and paths remain organized. |
| R-050 | Apply filters or edits, use Undo and Redo endpoints/UI if exposed. | State rolls back and reapplies without corrupting session. |
| R-051 | Load primary video and secondary/compare video. | Secondary path/session is accepted and compare tools can reference it. |
| R-052 | Apply filters, geometry correction, and reset/re-render. | Original/master frame remains recoverable; edits are non-destructive. |
| R-060 | Legal Export: choose Auto GPU or GPU codec on capable hardware. | GPU encoder is selected if available; CPU fallback works otherwise. |
| R-070 | Timeline Pro: load video and inspect timestamps. | Timestamp/PTS metadata is extracted. |
| R-071 | Run stream analysis/demux on video. | Stream list or demux result appears without crashing. |
| R-072 | Timeline/Stream Analysis: analyze I/P/B frames. | Frame type distribution is shown. |
| R-073 | Inspect frame metadata and filter/seek by frame/time. | Per-frame metadata appears and selected frame loads. |
| R-074 | Forensic Tools: run MPEG macroblock or motion visualization. | Overlay preview appears or codec limitation is reported. |
| R-075 | Timeline Pro: seek by time, frame, and nearest I-frame. | Preview jumps to expected frame/time. |
| R-080 | Video Tools: draw tracking box, run tracking, inspect key/auto tracking result. | Track result contains frames/boxes or clear failure reason. |
| R-081 | Save tracking data, reload it, then reuse for stabilization/export. | Saved tracking JSON reloads and drives later operation. |
| R-082 | Markup Studio: use arrow, rectangle, line, text, measure, redact. | Each tool draws at cursor and appears in annotation list. |
| R-083 | Add annotations on a frame and apply to frame/export. | Annotation burns/applies to current frame and persists. |
| R-084 | Add multiple annotations with same group ID. | Group ID is stored and shown for grouped annotations. |
| R-085 | Enable snap/guides and draw annotations/measurements. | Points snap to grid/guides consistently. |
| R-090 | Forensic Tools: choose AI enhancement and apply to frame. | Preview changes and operation completes. |
| R-091 | Import/select ONNX model path where available. | Model import path accepts valid model or reports runtime dependency. |
| R-100 | Settings: change UI/report language. | UI/report strings switch to selected locale where translated. |
| R-101 | Settings: enable accessibility/high contrast/color-vision/text-size options. | UI updates without layout breakage. |
| R-110 | Load video and extract audio stream. | Audio output file is created. |
| R-111 | Use audio player volume and mute controls. | Volume changes/mute state affects playback. |
| R-112 | Timeline Pro: step frame-by-frame while synced audio is available. | Frame time and audio sync metadata stay aligned. |
| R-113 | Inspect audio channels for a multichannel sample. | Channel list/metadata is returned. |
| R-114 | Add an audio redaction/mute region and export. | Selected region is muted in output. |
| R-115 | Add or replace an audio stream with external audio. | Output video contains selected audio stream. |
| R-116 | Apply A/V offset and export/mux. | Output uses requested offset. |
| R-117 | Mux shorter/longer audio and use pad-video option. | Output duration is reconciled by padding where requested. |
| R-120 | Load SRT/SMI subtitle and preview/burn. | Subtitle appears at expected timestamp. |
| R-121 | Change subtitle font/position/style and burn. | Output reflects selected subtitle style. |
| R-122 | Apply timestamp overlay with selected format/position. | Timestamp appears on preview/exported frame. |
| R-123 | Enable grid overlay and burn/apply. | Grid appears with selected preset/opacity. |
| R-124 | Video Tools: browse second video, preview side-by-side, export compare JPEG. | Side-by-side preview appears and JPEG export file is written. |
| R-125 | Video Tools: set PiP source, position/scale, apply/export. | Inset appears in chosen corner and composed frame exports. |
| R-130 | Case Reports: generate HTML/PDF/DOCX report. | Requested report files are written. |
| R-131 | Case Reports: switch paper size A4/Letter/Legal/A3. | Generated report uses selected page size. |
| R-132 | Case Reports: switch template type. | Report content/layout follows selected template. |
| R-133 | Run secure copy and include/cross-reference in report workflow. | Secure copy report exists and can be attached/referenced. |
| R-134 | Forensic Tools: copy/export current frame to office/clipboard path. | Frame copy/export succeeds. |
| R-140 | Hash Evidence File. | MD5, SHA-1, SHA-256, SHA-512 are shown. |
| R-141 | Hash current frame. | Frame-level hash is returned for loaded frame. |
| R-142 | Secure Copy + Report. | Copied file hash matches source and report is generated. |
| R-143 | Ingest, enhance, export, then open Chain of Custody. | Custody log records actions with time/actor/file. |
| R-144 | Perform several operations and inspect audit log output. | Audit entries are appended with action details. |
| R-145 | Legal Export: scan secure media folder, load references, batch export. | Manifest and verified batch export files are created. |
| R-150 | Apply deinterlace/interlace conversion to sample. | Output frame/video visibly changes or export succeeds. |
| R-151 | Apply lens/geometric distortion correction. | Corrected preview/output is generated. |
| R-152 | Geometry Correction: Omnidirectional -> Panorama; preview/apply/save. | Panoramic/rectilinear output changes and JPEG is written. |
| R-153 | Apply Homomorphic/Retinex/Adaptive illumination correction. | Uneven lighting changes and filter is recorded. |
| R-154 | Apply auto contrast/brightness/levels. | Tone changes with no crash and can reset. |
| R-155 | Apply color channel separation/isolation. | Selected channel/component is isolated or adjusted. |
| R-156 | Apply motion deblur/defocus deblur. | Restored/sharpened output is produced. |
| R-157 | Attempt multi-image perspective alignment with planned test case. | Currently planned; acceptance requires multi-image input workflow. |
| R-158 | Run perspective stabilization on video. | Stabilized output is produced or limitation is clearly reported. |
| R-159 | Load video frame, apply Super Resolution. | Frame dimensions/detail increase and preview updates. |
| R-160 | Run video stabilization/deshake or tracking stabilization. | Stabilized video export exists. |
| R-161 | Export FPS-adjusted video using duplicate/drop method. | Output FPS matches selected target. |
| R-162 | Manually set target FPS and export. | Output uses target FPS. |
| R-163 | Redact/blur/pixelate a region. | Region is obscured in preview/export. |
| R-164 | Create freeze-frame/placeholder video segment. | Output holds selected frame for requested duration. |
| R-165 | Reverse video playback/export. | Output plays in reverse order. |
| R-166 | Apply JPEG artifact reduction. | Compression artifacts are reduced or output changes visibly. |
| R-167 | Apply channel invert/replace. | Selected channel operation is visible. |
| R-170 | Markup Studio: measure line with calibration and error fields. | Distance includes selected unit and +/- uncertainty. |
| R-171 | Measure object displacement with delta time/speed field. | Speed is computed with uncertainty. |
| R-172 | Run stream sync/similarity on two media streams. | Similarity/sync score is returned. |
| R-173 | Merge or sequence multiple video/audio streams. | Merged output file exists. |
| R-174 | Load VFR sample and seek/play by timestamp. | VFR is detected and timestamp/PTS seeking works. |
| R-175 | Edit timestamp overlay and run region analysis. | Timestamp applies and region analysis table appears. |
| R-180 | Live Capture: start webcam/backend device. | Live preview appears. |
| R-181 | Build video from image sequence folder. | Output MP4 is created from frames. |
| R-182 | Live Capture: select live filter and preview. | Stream updates with selected filter. |
| R-183 | Live Capture: record 5s screen. | Screen capture file is created. |
| R-190 | Run Windows 64-bit package/install workflow. | App installs/starts on Windows 64-bit. |
| R-191 | Run 32-bit build profile on compatible Windows environment. | Build artifact is produced or dependency limitation documented. |
| R-192 | Enable operation logging and perform actions. | Log file records operations. |
| R-193 | Export VMS-compatible H.264/yuv420p/faststart video and test in target VMS/player. | Export plays in target player/VMS. |
| R-194 | Export external metadata via FFprobe/EXIF. | Metadata JSON/file is generated. |
| R-195 | Open Notes, add linked note, reload project. | Note persists in project state. |
| R-196 | Open example workflows/resources. | Example project/workflow is accessible and loadable. |

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
| Video overlays and side-by-side comparison | Implemented | `VideoOverlayComparePanel.jsx`, compare library, `/api/capabilities/compare/export-image` | Examination Lab -> Video Tools -> compare/overlay -> Preview compare -> Export compare JPEG | Side-by-side/PiP overlay previews and a JPEG export file is written |
| PiP display | Implemented | Video overlay compare settings, `draw_pip` | Enable PiP mode, choose position, preview/export | PiP appears in selected position and exports as a composed frame |
| Geometric distortion/perspective correction | Implemented | `PerspectiveCorrectionPanel.jsx`, `geo_keystone`, `both_perspective_match` | Geometry Correction -> Perspective correction -> drag corners -> Preview/Apply | Corrected preview appears; Apply updates frame; Revert correction restores |
| Panoramic / omnidirectional conversion | Implemented | `src/aive/panorama.py`, `PanoramaConversionPanel.jsx`, `adv_omni_panorama` | Geometry Correction -> Omnidirectional -> Panorama; choose fisheye or equirectangular, output type, yaw/pitch/roll, size; Preview/Apply/Save | Preview/apply produces flattened panorama or rectilinear perspective view; JPEG export is written |
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

Video overlay / PiP composition:

```bash
PYTHONPATH=src pytest tests/test_compare_overlays.py -q
```

Panoramic / omnidirectional conversion:

```bash
PYTHONPATH=src pytest tests/test_panorama_conversion.py -q
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
