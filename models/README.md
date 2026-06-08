# Custom AI / ONNX models (R-091)

Place `.onnx` files here or import via **Forensic Tools → AI / ML Enhancement**.

## Install ONNX runtime

```bash
pip install "onnxruntime>=1.19"
# or
pip install -e ".[ai]"
```

## Import in the app

1. **UI:** Forensic Tools → AI / ML → **Import ONNX model** (choose `.onnx` file).
2. **API:** `POST /api/ai/models/import` (multipart file upload).
3. **API (path):** `POST /api/ai/models/import-path` with JSON `{ "path": "/full/path/model.onnx" }`.

Models are stored under `~/.chakshu/models/` with a sidecar `{id}.json` manifest.

## Optional manifest (`my_model.json`)

```json
{
  "id": "my_denoiser",
  "name": "CCTV Denoiser",
  "task": "denoise",
  "input_size": [256, 256],
  "input_layout": "NCHW",
  "scale_output": true,
  "description": "Trained for H.264 night footage"
}
```

Pair with `my_denoiser.onnx` in the same folder.

## Supported tasks

| task | Use |
|------|-----|
| `enhance` | General quality improvement |
| `denoise` | Noise reduction |
| `deblur` | Blur reduction |
| `upscale` | Super-resolution |
| `custom` | Any image-to-image ONNX |

Input/output: RGB/BGR image tensors; the runtime resizes to `input_size` and scales back to the original frame size.

## Built-in tools (no model file)

- **auto_enhance** — denoise + CLAHE + sharpen  
- **low_light** — shadow lift for dark video  
- **denoise_ai** / **deblur_ai** / **super_resolution** — classical CV pipelines  

Use **Apply to current frame** in Examination Lab after loading evidence.
