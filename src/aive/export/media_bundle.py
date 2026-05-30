"""Export original and processed media with configurable encoding."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aive.export.exporter import ExportOptions, FrameRateMode, VideoExporter
from aive.gpu.encode import select_encoder


@dataclass
class MediaExportBundle:
    input_path: Path
    output_dir: Path
    include_original: bool = True
    include_processed: bool = True
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    use_stream_copy: bool = False
    frame_rate_mode: str = "cfr"
    fps: float | None = 29.97
    prefer_h265: bool = False
    image_quality: int = 90


def export_media_bundle(
    input_path: Path,
    processed_path: Path | None,
    bundle: MediaExportBundle,
) -> dict[str, Any]:
    bundle.output_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {"success": True, "files": []}

    if bundle.include_original and input_path.exists():
        orig_out = bundle.output_dir / f"original_{input_path.name}"
        if input_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}:
            shutil.copy2(input_path, orig_out)
        else:
            shutil.copy2(input_path, orig_out)
        results["files"].append({"role": "original", "path": str(orig_out)})

    proc_source = processed_path or input_path
    if bundle.include_processed:
        codec, _ = select_encoder(prefer_h265=bundle.prefer_h265)
        gpu = codec if any(x in codec for x in ("nvenc", "qsv", "amf")) else None
        ext = input_path.suffix or ".mp4"
        proc_out = bundle.output_dir / f"processed_{input_path.stem}{ext}"
        exporter = VideoExporter()
        if proc_source.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}:
            shutil.copy2(proc_source, bundle.output_dir / f"processed_{proc_source.name}")
            results["files"].append({"role": "processed", "path": str(bundle.output_dir / f"processed_{proc_source.name}")})
        else:
            opts = ExportOptions(
                output_path=proc_out,
                video_codec=codec,
                gpu_encoder=gpu,
                audio_codec=bundle.audio_codec,
                use_stream_copy=bundle.use_stream_copy,
                frame_rate_mode=FrameRateMode(bundle.frame_rate_mode),
                fps=bundle.fps,
            )
            exp = exporter.export(proc_source, opts)
            if exp.get("success"):
                results["files"].append({"role": "processed", "path": str(proc_out)})
            else:
                results["success"] = False
                results["error"] = exp.get("stderr", "Export failed")

    results["output_dir"] = str(bundle.output_dir)
    return results
