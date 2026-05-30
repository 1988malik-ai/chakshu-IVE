"""AI/ML enhancement and custom ONNX model integration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from aive.imaging import HAS_CV2, apply_basic_filter

if HAS_CV2:
    import cv2


@dataclass
class AIModelInfo:
    id: str
    name: str
    path: Path
    input_size: tuple[int, int] = (256, 256)
    task: str = "enhance"  # enhance | denoise | upscale | deblur | custom


class AIModelRegistry:
    def __init__(self, models_dir: Path | None = None) -> None:
        self.models_dir = models_dir or Path(__file__).resolve().parents[3] / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._models: dict[str, AIModelInfo] = {}
        self._sessions: dict[str, Any] = {}
        self._scan_builtin()

    def _scan_builtin(self) -> None:
        for onnx in self.models_dir.glob("*.onnx"):
            self.register(
                AIModelInfo(
                    id=onnx.stem,
                    name=onnx.stem.replace("_", " ").title(),
                    path=onnx,
                )
            )

    def register(self, info: AIModelInfo) -> None:
        self._models[info.id] = info

    def import_model(self, source: Path, model_id: str | None = None) -> AIModelInfo:
        dest = self.models_dir / source.name
        if source.resolve() != dest.resolve():
            dest.write_bytes(source.read_bytes())
        info = AIModelInfo(id=model_id or source.stem, name=source.stem, path=dest)
        self.register(info)
        return info

    def list_models(self) -> list[AIModelInfo]:
        return list(self._models.values())

    def _get_session(self, model_id: str):
        if model_id in self._sessions:
            return self._sessions[model_id]
        try:
            import onnxruntime as ort

            info = self._models[model_id]
            session = ort.InferenceSession(str(info.path), providers=["CPUExecutionProvider"])
            self._sessions[model_id] = session
            return session
        except ImportError:
            return None

    def run_enhance(self, frame: np.ndarray, model_id: str = "default") -> np.ndarray:
        if model_id not in self._models:
            return self._fallback_enhance(frame)
        session = self._get_session(model_id)
        if session is None:
            return self._fallback_enhance(frame)
        info = self._models[model_id]
        h, w = info.input_size
        if HAS_CV2:
            resized = cv2.resize(frame, (w, h))
        else:
            from PIL import Image

            rgb = frame[:, :, ::-1]
            resized = np.array(Image.fromarray(rgb).resize((w, h)))[:, :, ::-1]
        blob = resized.astype(np.float32) / 255.0
        blob = np.transpose(blob, (2, 0, 1))[np.newaxis, ...]
        input_name = session.get_inputs()[0].name
        out = session.run(None, {input_name: blob})[0]
        if out.ndim == 4:
            out = out[0]
        out = np.transpose(out, (1, 2, 0))
        out = np.clip(out * 255, 0, 255).astype(np.uint8)
        if HAS_CV2:
            return cv2.resize(out, (frame.shape[1], frame.shape[0]))
        from PIL import Image

        return np.array(Image.fromarray(out[:, :, ::-1]).resize(
            (frame.shape[1], frame.shape[0])
        ))[:, :, ::-1]

    @staticmethod
    def _fallback_enhance(frame: np.ndarray) -> np.ndarray:
        return apply_basic_filter(frame, "both_enhance_ai", {})
