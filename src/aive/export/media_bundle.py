"""Export original and processed media with configurable encoding."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aive.export.exporter import ExportOptions, FrameRateMode, VideoExporter
from aive.gpu.encode import select_encoder
from aive.imaging import save_bgr_jpeg


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".heic", ".heif"}


@dataclass
class MediaExportBundle:
    input_path: Path
    output_dir: Path
    original_dir: Path | None = None
    processed_dir: Path | None = None
    include_original: bool = True
    include_processed: bool = True
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    use_stream_copy: bool = False
    frame_rate_mode: str = "cfr"
    fps: float | None = 29.97
    prefer_h265: bool = False
    prefer_gpu: bool = True
    image_quality: int = 92
    crf: int | None = 23
    video_bitrate: str | None = None
    encode_preset: str = "medium"
    use_session_enhancement: bool = True


def _is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_SUFFIXES


def _resolve_encoder(bundle: MediaExportBundle) -> tuple[str, str | None]:
    if bundle.use_stream_copy or bundle.video_codec == "copy":
        return "copy", None
    if bundle.video_codec == "auto_gpu" or (bundle.prefer_gpu and bundle.video_codec in ("libx264", "libx265", "auto")):
        codec, _ = select_encoder(prefer_h265=bundle.prefer_h265)
        gpu = codec if any(x in codec for x in ("nvenc", "qsv", "amf")) else None
        return codec, gpu
    return bundle.video_codec, None


def _export_options(bundle: MediaExportBundle, output_path: Path) -> ExportOptions:
    codec, gpu = _resolve_encoder(bundle)
    return ExportOptions(
        output_path=output_path,
        video_codec=codec,
        gpu_encoder=gpu,
        audio_codec=bundle.audio_codec,
        use_stream_copy=bundle.use_stream_copy or codec == "copy",
        frame_rate_mode=FrameRateMode(bundle.frame_rate_mode),
        fps=bundle.fps,
        crf=bundle.crf,
        video_bitrate=bundle.video_bitrate,
        encode_preset=bundle.encode_preset,
    )


def export_media_bundle(
    input_path: Path,
    processed_path: Path | None,
    bundle: MediaExportBundle,
    *,
    session=None,
) -> dict[str, Any]:
    bundle.output_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {"success": True, "files": []}

    if not input_path.exists():
        return {"success": False, "error": f"Input not found: {input_path}", "files": []}

    orig_dir = bundle.original_dir or bundle.output_dir
    proc_dir = bundle.processed_dir or bundle.output_dir
    orig_dir.mkdir(parents=True, exist_ok=True)
    proc_dir.mkdir(parents=True, exist_ok=True)

    stem = input_path.stem
    is_image = _is_image(input_path)

    if bundle.include_original:
        orig_out = orig_dir / f"original_{input_path.name}"
        if session is not None and session.master_frame is not None and is_image:
            save_bgr_jpeg(orig_out.with_suffix(".jpg"), session.master_frame, bundle.image_quality)
            results["files"].append({"role": "original", "path": str(orig_out.with_suffix(".jpg")), "source": "session_master"})
        else:
            shutil.copy2(input_path, orig_out)
            results["files"].append({"role": "original", "path": str(orig_out), "source": "file_copy"})

    if bundle.include_processed:
        wrote_session = False
        if (
            bundle.use_session_enhancement
            and session is not None
            and session.frame is not None
            and session.filter_chain
        ):
            proc_img = proc_dir / f"processed_{stem}_examination.jpg"
            save_bgr_jpeg(proc_img, session.frame, bundle.image_quality)
            results["files"].append({
                "role": "processed",
                "path": str(proc_img),
                "source": "session_enhanced_frame",
            })
            wrote_session = True

        proc_source = processed_path or input_path
        if is_image and not wrote_session:
            proc_out = proc_dir / f"processed_{proc_source.name}"
            if session is not None and session.frame is not None and session.filter_chain:
                save_bgr_jpeg(proc_out.with_suffix(".jpg"), session.frame, bundle.image_quality)
                results["files"].append({"role": "processed", "path": str(proc_out.with_suffix(".jpg")), "source": "session_frame"})
            else:
                shutil.copy2(proc_source, proc_out)
                results["files"].append({"role": "processed", "path": str(proc_out), "source": "file_copy"})
        elif not is_image:
            ext = input_path.suffix or ".mp4"
            proc_out = proc_dir / f"processed_{stem}{ext}"
            opts = _export_options(bundle, proc_out)
            exporter = VideoExporter()
            exp = exporter.export(proc_source, opts)
            if exp.get("success"):
                results["files"].append({"role": "processed", "path": str(proc_out), "source": "reencoded"})
            else:
                results["success"] = False
                results["error"] = exp.get("stderr") or exp.get("error") or "Export failed"

    results["output_dir"] = str(bundle.output_dir)
    results["original_dir"] = str(orig_dir)
    results["processed_dir"] = str(proc_dir)
    return results
