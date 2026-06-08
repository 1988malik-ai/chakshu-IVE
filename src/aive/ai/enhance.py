"""AI enhancement facade — built-in tools + optional ONNX models (R-090, R-091)."""

from __future__ import annotations

from typing import Any

import numpy as np

from aive.ai.models import get_registry
from aive.imaging import HAS_CV2

if HAS_CV2:
    import cv2

BUILTIN_TOOLS: dict[str, dict[str, Any]] = {
    "auto_enhance": {
        "name": "Auto Enhance (AI-style)",
        "description": "Denoise, local contrast (CLAHE), and edge recovery — no model file required.",
        "task": "enhance",
        "requires_model": False,
    },
    "low_light": {
        "name": "Low-Light Recovery",
        "description": "Lift shadows and normalize exposure for dark CCTV / night footage.",
        "task": "enhance",
        "requires_model": False,
    },
    "denoise_ai": {
        "name": "AI Denoise",
        "description": "Strong temporal-style denoise for noisy compression artifacts.",
        "task": "denoise",
        "requires_model": False,
    },
    "deblur_ai": {
        "name": "AI Deblur",
        "description": "Sharpen and reduce motion / defocus blur (classical + optional ONNX).",
        "task": "deblur",
        "requires_model": False,
    },
    "super_resolution": {
        "name": "Super-Resolution Preview",
        "description": "Upscale detail preview; use a custom ONNX SR model for best quality.",
        "task": "upscale",
        "requires_model": False,
    },
    "custom_onnx": {
        "name": "Custom ONNX Model",
        "description": "Run an imported .onnx model (denoise, enhance, upscale, etc.).",
        "task": "custom",
        "requires_model": True,
    },
}


def list_tools() -> list[dict[str, Any]]:
    reg = get_registry()
    tools = [{**meta, "id": tid} for tid, meta in BUILTIN_TOOLS.items()]
    for m in reg.list_models():
        tools.append(
            {
                "id": f"model:{m.id}",
                "name": m.name,
                "description": f"Custom ONNX — {m.task}",
                "task": m.task,
                "requires_model": True,
                "model_id": m.id,
            }
        )
    return tools


def _unsharp(frame: np.ndarray, amount: float = 0.35, sigma: float = 3.0) -> np.ndarray:
    blurred = cv2.GaussianBlur(frame, (0, 0), sigma)
    return cv2.addWeighted(frame, 1 + amount, blurred, -amount, 0)


def _clahe(frame: np.ndarray, clip: float = 2.5) -> np.ndarray:
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def _builtin_auto(frame: np.ndarray, strength: float) -> np.ndarray:
    h = max(3, int(5 * strength))
    out = cv2.fastNlMeansDenoisedColored(frame, None, h, h, 7, 21)
    return _unsharp(_clahe(out, 2.0 + strength), 0.25 + 0.2 * strength)


def _builtin_low_light(frame: np.ndarray, strength: float) -> np.ndarray:
    gamma = 1.0 / max(0.5, 1.0 - 0.15 * strength)
    inv = 1.0 / gamma
    lut = np.array([((i / 255.0) ** inv) * 255 for i in range(256)], dtype=np.uint8)
    lifted = cv2.LUT(frame, lut)
    return _clahe(lifted, 3.0 + strength)


def _builtin_denoise(frame: np.ndarray, strength: float) -> np.ndarray:
    h = max(5, int(8 * strength))
    return cv2.fastNlMeansDenoisedColored(frame, None, h, h, 7, 21)


def _builtin_deblur(frame: np.ndarray, strength: float) -> np.ndarray:
    amount = 0.5 + 0.8 * strength
    return _unsharp(_builtin_denoise(frame, 0.5), amount, 2.0)


def _builtin_super_res(frame: np.ndarray, strength: float) -> np.ndarray:
    scale = 1.0 + 0.25 * min(strength, 2.0)
    h, w = frame.shape[:2]
    nh, nw = int(h * scale), int(w * scale)
    up = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_CUBIC)
    return cv2.resize(up, (w, h), interpolation=cv2.INTER_AREA)


def _builtin_run(tool: str, frame: np.ndarray, strength: float) -> np.ndarray:
    if not HAS_CV2:
        from aive.imaging import apply_basic_filter

        return apply_basic_filter(frame, "both_enhance_ai", {"strength": strength})
    runners = {
        "auto_enhance": _builtin_auto,
        "low_light": _builtin_low_light,
        "denoise_ai": _builtin_denoise,
        "deblur_ai": _builtin_deblur,
        "super_resolution": _builtin_super_res,
    }
    fn = runners.get(tool, _builtin_auto)
    return fn(frame, max(0.1, min(float(strength), 3.0)))


def run_ai_tool(frame: np.ndarray, params: dict[str, Any] | None = None) -> np.ndarray:
    """Apply AI tool to BGR frame. Params: tool, model_id, strength."""
    p = params or {}
    tool = str(p.get("tool") or p.get("ai_tool") or "auto_enhance")
    model_id = str(p.get("model_id") or "").strip()
    strength = float(p.get("strength", 1.0))

    if tool.startswith("model:"):
        model_id = tool.split(":", 1)[1]
        tool = "custom_onnx"

    reg = get_registry()
    if model_id and model_id in {m.id for m in reg.list_models()}:
        return reg.run_enhance(frame, model_id, strength=strength)

    if tool == "custom_onnx":
        if model_id:
            return reg.run_enhance(frame, model_id, strength=strength)
        return _builtin_run("auto_enhance", frame, strength)

    return _builtin_run(tool, frame, strength)


def onnx_runtime_available() -> bool:
    try:
        import onnxruntime  # noqa: F401

        return True
    except ImportError:
        return False
