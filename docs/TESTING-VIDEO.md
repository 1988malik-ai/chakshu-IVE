# Testing Video in AI-IVE Forensics

**Author:** Mohit M

## Prerequisites

1. **FFmpeg** (all platforms — no Homebrew):

   ```bash
   pip install -r requirements-video.txt
   python scripts/check-media-deps.py
   ```

   See **`docs/FFMPEG-CROSS-PLATFORM.md`** for Windows/Linux/macOS details.

2. **OpenCV** (recommended):

   ```bash
   pip install opencv-python-headless
   ```

3. **API + UI running:**

   ```bash
   cd ~/Desktop/AI-IVE
   export PYTHONPATH=src
   python3 -m aive.api.server

   # other terminal
   cd frontend && npm run dev
   ```

4. Open **http://localhost:9451** → Examination Lab.

## Method A — Upload (recommended)

1. Click **Ingest Evidence** and choose an `.mp4` / `.mov` file.
2. You should see:
   - Status: `Video ingested: yourfile.mp4`
   - **VIDEO** badge on the preview panel
   - HTML5 **video player** under the frame preview
   - **Scrub frame** slider + **Load Frame at Time**

3. Scrub the slider → click **Load Frame at Time** → the still image above updates (filters apply to that frame).

4. **Forensic Tools** tab: hash/seek/trim use the saved path automatically (`storage_path` under `~/.ai-ive/cases/.../evidence/`).

## Method B — Load by full path

If upload fails or tools say "file not found":

1. Paste the **full path** in **LOAD BY FULL PATH**, e.g. `/Users/you/Desktop/sample.mp4`
2. Click **Load Path**

## Verify API directly

```bash
# Health
curl -s http://localhost:9450/api/health

# Create session
SID=$(curl -s -X POST http://localhost:9450/api/session | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")

# Upload video
curl -s -X POST "http://localhost:9450/api/media/upload?session_id=$SID" \
  -F "file=@/path/to/your/video.mp4" | python3 -m json.tool

# Expect: "media_type": "video", "storage_path": "/Users/.../.ai-ive/cases/.../evidence/....mp4", "preview": "<base64>"

# Seek frame at 5 seconds
curl -s -X POST http://localhost:9450/api/media/seek \
  -H 'Content-Type: application/json' \
  -d "{\"session_id\":\"$SID\",\"time_sec\":5.0}" | python3 -c "import sys,json; d=json.load(sys.stdin); print('ok' if d.get('preview') else d)"
```

## Common failures

| Symptom | Fix |
|--------|-----|
| `Could not decode image` on upload | Restart API after update; ensure FFmpeg installed |
| Video player empty | Check `storage_path` in upload JSON; path must exist under `~/.ai-ive` |
| Seek/trim 404 | Use **full path** from `storage_path`, not filename only |
| No OpenCV | OK if FFmpeg works; install opencv for faster local decode |
