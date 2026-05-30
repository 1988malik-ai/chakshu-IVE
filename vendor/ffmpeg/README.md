# Optional manual FFmpeg binaries

Normally you do **not** need this folder — use:

```bash
pip install -r requirements-video.txt
```

If you are offline, place platform binaries here:

- `macos-arm64/ffmpeg` (+ optional `ffprobe`)
- `macos-x64/ffmpeg`
- `win64/ffmpeg.exe`
- `linux-x64/ffmpeg`

See `docs/FFMPEG-CROSS-PLATFORM.md`.
