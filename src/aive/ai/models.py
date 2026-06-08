"""AI/ML enhancement and custom ONNX model integration (R-090, R-091)."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from aive.imaging import HAS_CV2

if HAS_CV2:
    import cv2

_REGISTRY: AIModelRegistry | None = None


@dataclass
class AIModelInfo:
    id: str
    name: str
    path: Path
    input_size: tuple[int, int] = (256, 256)
    task: str = "enhance"  # enhance | denoise | upscale | deblur | super_resolution | custom
    input_layout: str = "NCHW"
    scale_output: bool = True
    description: str = ""
    imported_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "path": str(self.path),
            "input_size": list(self.input_size),
            "task": self.task,
            "input_layout": self.input_layout,
            "scale_output": self.scale_output,
            "description": self.description,
            "imported_at": self.imported_at,
            "onnx": self.path.suffix.lower() == ".onnx",
        }


class AIModelRegistry:
    def __init__(self, models_dir: Path | None = None) -> None:
        self.models_dir = models_dir or Path.home() / ".chakshu" / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._models: dict[str, AIModelInfo] = {}
        self._sessions: dict[str, Any] = {}
        self._scan_models()

    def _manifest_path(self, model_id: str) -> Path:
        return self.models_dir / f"{model_id}.json"

    def _scan_models(self) -> None:
        for meta in self.models_dir.glob("*.json"):
            try:
                raw = json.loads(meta.read_text(encoding="utf-8"))
                onnx = self.models_dir / f"{raw['id']}.onnx"
                if not onnx.exists():
                    onnx = Path(raw.get("path", ""))
                if onnx.exists():
                    self.register(self._info_from_manifest(raw, onnx))
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
        for onnx in self.models_dir.glob("*.onnx"):
            if onnx.stem not in self._models:
                self.register(
                    AIModelInfo(
                        id=onnx.stem,
                        name=onnx.stem.replace("_", " ").title(),
                        path=onnx,
                    )
                )

    @staticmethod
    def _info_from_manifest(raw: dict[str, Any], path: Path) -> AIModelInfo:
        sz = raw.get("input_size", [256, 256])
        if isinstance(sz, (list, tuple)) and len(sz) >= 2:
            input_size = (int(sz[0]), int(sz[1]))
        else:
            input_size = (256, 256)
        return AIModelInfo(
            id=str(raw["id"]),
            name=str(raw.get("name", raw["id"])),
            path=path,
            input_size=input_size,
            task=str(raw.get("task", "enhance")),
            input_layout=str(raw.get("input_layout", "NCHW")),
            scale_output=bool(raw.get("scale_output", True)),
            description=str(raw.get("description", "")),
            imported_at=str(raw.get("imported_at", datetime.utcnow().isoformat())),
        )

    def _persist_manifest(self, info: AIModelInfo) -> None:
        data = info.to_dict()
        data.pop("onnx", None)
        self._manifest_path(info.id).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def register(self, info: AIModelInfo) -> None:
        self._models[info.id] = info
        self._persist_manifest(info)

    def import_model(
        self,
        source: Path,
        model_id: str | None = None,
        name: str | None = None,
        task: str = "enhance",
        input_size: tuple[int, int] = (256, 256),
        description: str = "",
    ) -> AIModelInfo:
        source = source.expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Model file not found: {source}")
        if source.suffix.lower() != ".onnx":
            raise ValueError("Only .onnx models are supported for custom import")

        mid = (model_id or source.stem).strip()
        mid = "".join(c if c.isalnum() or c in "-_" else "_" for c in mid)
        dest = self.models_dir / f"{mid}.onnx"
        if source != dest:
            shutil.copy2(source, dest)

        info = AIModelInfo(
            id=mid,
            name=name or mid.replace("_", " ").title(),
            path=dest,
            input_size=input_size,
            task=task,
            description=description or f"Imported from {source.name}",
        )
        self.register(info)
        self._sessions.pop(mid, None)
        return info

    def delete_model(self, model_id: str) -> bool:
        if model_id not in self._models:
            return False
        info = self._models.pop(model_id)
        self._sessions.pop(model_id, None)
        if info.path.exists():
            info.path.unlink(missing_ok=True)
        manifest = self._manifest_path(model_id)
        if manifest.exists():
            manifest.unlink()
        return True

    def list_models(self) -> list[AIModelInfo]:
        self._scan_models()
        return list(self._models.values())

    def get(self, model_id: str) -> AIModelInfo | None:
        self._scan_models()
        return self._models.get(model_id)

    def _get_session(self, model_id: str):
        if model_id in self._sessions:
            return self._sessions[model_id]
        try:
            import onnxruntime as ort

            info = self._models[model_id]
            session = ort.InferenceSession(
                str(info.path),
                providers=["CPUExecutionProvider"],
            )
            self._sessions[model_id] = session
            return session
        except ImportError:
            return None
        except Exception:
            return None

    def run_enhance(
        self,
        frame: np.ndarray,
        model_id: str,
        strength: float = 1.0,
    ) -> np.ndarray:
        from aive.ai.enhance import _builtin_run

        if model_id not in self._models:
            return _builtin_run("auto_enhance", frame, strength)
        session = self._get_session(model_id)
        if session is None:
            return _builtin_run("auto_enhance", frame, strength)

        info = self._models[model_id]
        h, w = frame.shape[:2]
        iw, ih = info.input_size

        if HAS_CV2:
            resized = cv2.resize(frame, (iw, ih))
        else:
            from PIL import Image

            rgb = frame[:, :, ::-1]
            resized = np.array(Image.fromarray(rgb).resize((iw, ih)))[:, :, ::-1]

        blob = resized.astype(np.float32)
        if info.scale_output:
            blob = blob / 255.0
        if info.input_layout.upper() == "NCHW":
            blob = np.transpose(blob, (2, 0, 1))[np.newaxis, ...]
        else:
            blob = blob[np.newaxis, ...]

        input_name = session.get_inputs()[0].name
        try:
            out = session.run(None, {input_name: blob})[0]
        except Exception:
            return _builtin_run("auto_enhance", frame, strength)

        if out.ndim == 4:
            out = out[0]
        if out.shape[0] in (1, 3) and out.ndim == 3:
            out = np.transpose(out, (1, 2, 0))
        if out.ndim == 2:
            out = np.stack([out, out, out], axis=-1)

        if info.scale_output and out.max() <= 1.5:
            out = np.clip(out * 255, 0, 255).astype(np.uint8)
        else:
            out = np.clip(out, 0, 255).astype(np.uint8)

        if out.shape[2] == 1:
            out = np.repeat(out, 3, axis=2)
        if HAS_CV2:
            return cv2.resize(out, (w, h))
        from PIL import Image

        return np.array(Image.fromarray(out[:, :, ::-1]).resize((w, h)))[:, :, ::-1]

    def status(self) -> dict[str, Any]:
        try:
            import onnxruntime as ort

            ort_ver = ort.__version__
            onnx_ok = True
        except ImportError:
            ort_ver = None
            onnx_ok = False
        return {
            "onnxruntime_available": onnx_ok,
            "onnxruntime_version": ort_ver,
            "models_dir": str(self.models_dir),
            "model_count": len(self.list_models()),
        }


def get_registry() -> AIModelRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = AIModelRegistry()
    return _REGISTRY
