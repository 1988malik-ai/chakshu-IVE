# AI / ML Support — Implementation Guide (R-090, R-091)

**Product:** Chakshu  
**Requirements:** AI-based enhancement tools; custom ONNX model import  

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Forensic UI    │────▶│  /api/ai/*       │────▶│  ai/enhance.py  │
│  Examination    │     │  routes_ai.py    │     │  run_ai_tool()  │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                    ┌──────────────────────────────────────┴──────────┐
                    ▼                                                  ▼
           Built-in tools (OpenCV)                          ai/models.py
           auto_enhance, low_light, …                       ONNX Runtime
```

| Module | Role |
|--------|------|
| `src/aive/ai/enhance.py` | Built-in “AI-style” tools (no model file) |
| `src/aive/ai/models.py` | Registry, import, ONNX inference |
| `src/aive/api/routes_ai.py` | REST API |
| `src/aive/filters/forensic_ops.py` | Catalog filters `both_enhance_ai` call `run_ai_tool()` |

---

## 1. Install ONNX (optional, for custom models)

```bash
cd ~/Desktop/AI-IVE
source .venv/bin/activate
pip install onnxruntime
# or: pip install -e ".[ai]"
```

Verify:

```bash
curl -s http://127.0.0.1:9450/api/ai/status
```

---

## 2. Use built-in AI tools (no import)

1. Start API + UI.
2. **Ingest** an image or video frame in Examination Lab.
3. Open **Forensic Tools → AI / ML Enhancement**.
4. Choose a tool (e.g. **Auto Enhance**, **Low-Light Recovery**).
5. Adjust **Strength** → **Apply to Frame**.

Or use filter search in Examination Lab: `enhance ai`, `denoise ai`, `deblur`.

---

## 3. Import a custom ONNX model (R-091)

### UI

Forensic Tools → **Import ONNX Model** → select `.onnx` file.

### API

```bash
curl -X POST http://127.0.0.1:9450/api/ai/models/import \
  -F "file=@/path/to/mydenoiser.onnx" \
  -F "name=CCTV Denoiser" \
  -F "task=denoise"
```

### Path on disk

```bash
curl -X POST http://127.0.0.1:9450/api/ai/models/import-path \
  -H "Content-Type: application/json" \
  -d '{"path":"/Users/you/models/sr.onnx","model_id":"sr_x2","task":"upscale","input_width":512,"input_height":512}'
```

Models are stored in `~/.chakshu/models/` with `{id}.onnx` + `{id}.json`.

See [`models/README.md`](../models/README.md) for manifest fields.

---

## 4. Apply custom model to current frame

```bash
curl -X POST http://127.0.0.1:9450/api/ai/enhance/session \
  -H "Content-Type: application/json" \
  -d '{"session_id":"<session-uuid>","tool":"custom_onnx","model_id":"sr_x2","strength":1.2}'
```

---

## 5. ONNX model expectations

- **Format:** ONNX (`.onnx`)
- **I/O:** Image tensor in → image tensor out (1×3×H×W or 1×H×W×3)
- **Values:** Float 0–1 if `scale_output: true` in manifest
- **Size:** Resized to `input_size` (default 256×256), then resized back to source frame

Training/export tips:

- Export with fixed spatial dims (e.g. 256×256) for simplest integration.
- Prefer models trained on BGR/RGB photo enhancement or denoising.
- Test with `onnxruntime` CLI before importing.

---

## 6. API reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/ai/status` | ONNX availability, model count |
| GET | `/api/ai/tools` | Built-in + registered model tools |
| GET | `/api/ai/models` | List imported models |
| POST | `/api/ai/models/import` | Upload `.onnx` |
| POST | `/api/ai/models/import-path` | Import from filesystem path |
| DELETE | `/api/ai/models/{id}` | Remove model |
| POST | `/api/ai/enhance/session` | Apply to examination session |

---

## 7. Compliance mapping

| ID | How we meet it |
|----|----------------|
| **R-090** | Six built-in AI-style tools + pipeline integration + UI |
| **R-091** | ONNX import (upload + path), registry, manifest, delete, inference |

---

**Author:** Mohit M  
**See also:** `docs/REQUIREMENTS-TEST-GUIDE.md` (R-090, R-091 rows)
