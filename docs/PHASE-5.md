# Phase 5 — Capture, Real-Time & Examples

**Product:** Chakshu  
**Author:** Mohit M  
**Status:** Implemented

---

## Delivered

| Requirement | Feature |
|-------------|---------|
| R-180 Live video capture | Browser webcam + OpenCV device MJPEG stream |
| R-181 Image sequences as video | `capture/sequence_video.py` + UI |
| R-182 Real-time stream processing | Live filter on MJPEG (`filter_id` query param) |
| R-183 Screen capture | FFmpeg avfoundation / gdigrab / x11grab |
| R-196 Example projects | `examples/workflows/*.yaml` + Command Center |

---

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /api/capture/devices` | List OpenCV capture devices |
| `GET /api/capture/stream/mjpeg` | Real-time MJPEG (optional `filter_id`) |
| `GET /api/capture/snapshot` | Single frame with optional filter |
| `POST /api/capture/ingest` | Snap → examination session |
| `POST /api/capture/screen` | Record screen to MP4 |
| `POST /api/capture/sequence/to-video` | Folder of images → MP4 |
| `GET /api/capture/examples` | List learning workflows |

---

## UI

- **Live Capture** nav tab — webcam, backend stream, screen record, sequence builder
- **Command Center** — example workflow cards with step lists
- Product branding: **Chakshu Forensics**

---

## How to use

1. Open **Live Capture**
2. **Browser Webcam** → Start → **Snap to Evidence**
3. Or **Backend Device** with optional live filter (requires OpenCV + camera)
4. **Record 5s Screen** — set output path, uses FFmpeg
5. **Image sequence → video** — point at frames folder

Example workflows live in `examples/workflows/`.
