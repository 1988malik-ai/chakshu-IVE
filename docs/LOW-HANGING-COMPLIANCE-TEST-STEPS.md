# Low-Hanging Compliance Test Steps

Use this checklist to verify the recently completed compliance hardening items:
R-014, R-022, R-041, R-111, and R-133.

## Setup

1. Start the backend and frontend.
   ```bash
   source .venv/bin/activate
   export PYTHONPATH=src
   python -m aive.api.server
   ```
   ```bash
   cd frontend
   npm run dev
   ```
2. Open `http://localhost:9451`.
3. Set a Case ID, then ingest one image and one video sample if available.
4. Keep a project output folder ready, for example `~/Desktop/CHK-TEST-001`.

## R-014 Standard Formats + System Codec Extension

Goal: confirm standard media formats and codec diagnostics are visible and actionable.

### UI Test

1. Open **Settings**.
2. Find **Media compatibility**.
3. Confirm these rows are visible:
   - FFmpeg / system codec extension
   - RAW camera formats
   - HEIC / HEIF
   - Accepted image formats
   - Accepted video formats
4. Open **Legal Export**.
5. Export a loaded video using a normal MP4/H.264 setting.
6. If available, repeat with an MKV/stream-copy style preset.

### API Test

```bash
curl -s http://127.0.0.1:9450/api/capabilities/media/formats
```

### Pass Criteria

- API returns `standard_images`, `specialized_images`, `raw`, `heif`, and `video`.
- FFmpeg status includes source/path diagnostics.
- MP4 export plays in VLC/QuickTime.
- Unsupported codecs fail with a clear diagnostic, not a generic crash.

## R-022 Import Projects From Compatible Tools

Goal: confirm compatible project files can be inspected before import.

### UI Test

1. Open **Settings**.
2. Find **Project import**.
3. Enter a path to an existing `.aive.yaml`, `.aive.yml`, or compatible `.json`.
4. Click **Inspect**.
5. Review:
   - Status
   - Format
   - Name
   - Media/filter/step/bookmark/note counts
   - Warnings
6. Click **Import project**.
7. Open **Command Center** or **Case Reports** and confirm the imported project context is active.

### API Test

```bash
curl -s -X POST http://127.0.0.1:9450/api/project/import/inspect \
  -H 'Content-Type: application/json' \
  -d '{"path":"~/Desktop/sample.aive.yaml"}'
```

```bash
curl -s -X POST http://127.0.0.1:9450/api/project/import \
  -H 'Content-Type: application/json' \
  -d '{"path":"~/Desktop/sample.aive.yaml"}'
```

### Pass Criteria

- Inspect returns `supported: true` for compatible files.
- Counts match the source project.
- Unsupported files return a readable compatibility error.
- Import updates the active project without losing existing app stability.

## R-041 RAW / Specialized Image Formats

Goal: confirm RAW/HEIC support is discoverable and missing dependencies are explained.

### UI Test

1. Open **Settings**.
2. Check **Media compatibility**.
3. Confirm RAW status shows either **Available** or **Needs setup**.
4. Try ingesting a `.dng`, `.cr2`, `.nef`, or `.arw` sample.
5. If `rawpy` is installed, confirm the preview loads.
6. If `rawpy` is not installed, confirm the toast says to install `rawpy`.

### API Test

```bash
curl -s http://127.0.0.1:9450/api/capabilities/media/formats
```

### Pass Criteria

- RAW extensions are listed in diagnostics.
- RAW files decode when `rawpy` is installed.
- Missing RAW dependency shows: `pip install rawpy`.
- HEIC/HEIF status shows `pillow-heif` guidance when needed.

## R-111 Playback Volume / Mute

Goal: confirm mute and volume state are consistent across audio surfaces.

### UI Test

1. Ingest a video with audio.
2. Open **Examination Lab**.
3. In **Evidence Path**, use the audio player:
   - lower volume
   - mute
   - unmute
4. Open **Timeline Pro**.
5. Click **Probe** under Audio & Sync.
6. Play the Timeline video.
7. Confirm Timeline video and synced audio obey the same mute/volume setting.
8. Change volume in Timeline.
9. Return to **Examination Lab** and confirm the Evidence Path audio player reflects the same setting.
10. Refresh the page and confirm the last volume/mute state persists.

### Pass Criteria

- Volume slider changes playback loudness.
- Mute silences Timeline video audio and synced audio player.
- Settings persist while switching tabs.
- Playback speed changes do not break audio controls.

## R-133 Secure Copy In Reports

Goal: confirm secure copy artifacts and hash report are included in generated reports.

### UI Test

1. Ingest evidence.
2. Open **Forensic Tools**.
3. Click **Hash Evidence File** and confirm hashes appear.
4. Click **Secure Copy + Report**.
5. Confirm status says secure copy verified.
6. Open **Case Reports**.
7. Set output directory to the case reports folder.
8. Select HTML, PDF, and DOCX if dependencies are available.
9. Click **Generate HTML / PDF / DOCX**.
10. Open the generated HTML report first.
11. Find **Secure Copy Verification**.

### Pass Criteria

- Secure copy file exists under the configured export folder.
- `copy-report.json` exists.
- Generated report includes:
  - source path
  - destination path
  - hash report path
  - verified status
- HTML always works.
- PDF/DOCX work when `reportlab` and `python-docx` are installed; otherwise UI reports the missing dependency.

## Quick Smoke Commands

Run these after code changes:

```bash
.venv/bin/python -m py_compile \
  src/aive/project/workflow.py \
  src/aive/api/routes_extended.py \
  src/aive/api/routes_capabilities.py \
  src/aive/media/capabilities.py \
  src/aive/api/session.py \
  src/aive/forensics/secure_copy.py \
  src/aive/reports/generator.py
```

```bash
cd frontend
npm run build
```

If `pytest` is installed:

```bash
.venv/bin/python -m pytest tests/test_import_media_secure_report.py -q
```
