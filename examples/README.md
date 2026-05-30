# Chakshu — Example Workflows

**Chakshu** is a digital media examination platform for forensic image and video analysis.

## Quick start

```bash
cd ~/Desktop/AI-IVE
export PYTHONPATH=src
python -m aive.api.server          # API :9450
cd frontend && npm run dev         # UI :9451
```

1. Open **Chakshu Forensics** in the browser.
2. **Ingest Evidence** — upload image or video.
3. Use **Examination Lab** filters, **Timeline Pro** for video, **Markup Studio** for annotations.
4. **Live Capture** — webcam or screen for real-time intake.

## Workflows

| Example | File | Description |
|---------|------|-------------|
| Image enhancement | `workflows/image-enhancement.yaml` | Load → CLAHE → sharpen → export |
| Video timeline | `workflows/video-timeline.yaml` | Deep index → I-frame step → region analysis |
| Live capture | `workflows/live-capture.yaml` | Webcam snap → ingest → markup |
| Hash & custody | `workflows/hash-custody.yaml` | Secure copy → multi-hash → custody log |

## Author

Mohit M
