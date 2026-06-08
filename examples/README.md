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

| Example | File | Test workflow |
|---------|------|---------------|
| Image enhancement | `workflows/image-enhancement.yaml` | **WF-02** in [`docs/WORKFLOW-TEST-GUIDE.md`](../docs/WORKFLOW-TEST-GUIDE.md) |
| Video timeline | `workflows/video-timeline.yaml` | **WF-03** |
| Live capture | `workflows/live-capture.yaml` | **WF-07** |
| Hash & custody | `workflows/hash-custody.yaml` | **WF-05** |

Full workflow test guide: [`docs/WORKFLOW-TEST-GUIDE.md`](../docs/WORKFLOW-TEST-GUIDE.md)

## Author

Mohit M
