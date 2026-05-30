# FFmpeg — cross-platform setup (no Homebrew required)

**Author:** Mohit M

AI-IVE needs **FFmpeg** for video ingest, seek, trim, audio export, and reports.  
You do **not** need Homebrew, MacPorts, or Xcode to run on **Windows, macOS, or Linux**.

---

## One command (recommended — all platforms)

From the project folder, with your venv active:

```bash
pip install -r requirements-video.txt
python scripts/check-media-deps.py
```

This installs **`imageio-ffmpeg`**, which ships a private FFmpeg binary for your OS (Windows / macOS Intel & ARM / Linux).

If you see `Video features: ready`, restart the API:

```bash
export PYTHONPATH=src
python -m aive.api.server
```

Check: `curl -s http://localhost:9450/api/health` → `"ffmpeg": true`

---

## Full install (Python + OpenCV + video)

```bash
./scripts/install.sh -y
source .venv/bin/activate
pip install -r requirements-video.txt
python scripts/check-media-deps.py
```

---

## Optional: point to your own FFmpeg

If your organisation already installs FFmpeg:

| Platform | Example |
|----------|---------|
| **macOS** | `export AIVE_FFMPEG_PATH="$HOME/bin/ffmpeg"` |
| **Windows** | `set AIVE_FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe` |
| **Linux** | `export AIVE_FFMPEG_PATH=/usr/bin/ffmpeg` |

Optional ffprobe:

```bash
export AIVE_FFPROBE_PATH=/path/to/ffprobe
```

Or edit `config/app.yaml`:

```yaml
ffmpeg:
  ffmpeg_path: /full/path/to/ffmpeg
  ffprobe_path: /full/path/to/ffprobe
```

---

## Optional: vendor folder (offline / air-gapped)

Drop binaries here (no pip network):

```
vendor/ffmpeg/
  macos-arm64/ffmpeg
  macos-x64/ffmpeg
  win64/ffmpeg.exe
  linux-x64/ffmpeg
```

Same folder can include `ffprobe` next to `ffmpeg`.

---

## Platform cheat sheet

| Platform | Easiest path | Avoid |
|----------|--------------|--------|
| **macOS 12+** | `pip install -r requirements-video.txt` | Broken/old Homebrew tier-3 builds |
| **macOS (manual)** | https://evermeet.cx/ffmpeg/ → `~/bin` + `AIVE_FFMPEG_PATH` | — |
| **Windows 10/11** | `pip install -r requirements-video.txt` | — |
| **Ubuntu/Debian** | `pip install -r requirements-video.txt` OR `sudo apt install ffmpeg` | — |
| **Docker** | Use `Dockerfile` (ffmpeg in image) | Host brew |

---

## What works without FFmpeg

| Feature | Without FFmpeg |
|---------|----------------|
| Images, filters, reports | Yes (Pillow / OpenCV) |
| Video upload preview | Only if OpenCV reads your codec |
| Seek, trim, I-frames, audio extract | No |

---

## Troubleshooting

```bash
python scripts/check-media-deps.py
```

| Output | Action |
|--------|--------|
| `FFmpeg: NO` | Run `pip install -r requirements-video.txt` |
| `source: imageio-ffmpeg` | Good — bundled binary in use |
| `source: PATH` | System FFmpeg — ensure it runs: `ffmpeg -version` |
| API still `ffmpeg: false` | Restart API after pip install |

---

## Team / CI tip

Pin video deps in CI:

```yaml
- run: pip install -r requirements-fast.txt -r requirements-video.txt
- run: python scripts/check-media-deps.py
```

Same steps on every developer machine → same behaviour on Windows, Mac, and Linux.
