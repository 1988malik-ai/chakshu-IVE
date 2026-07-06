"""
R-145 — Direct load from secure media and batch export with hash validation.

Scans nested folders on read-only / secure volumes, registers evidence by reference,
and batch-exports with per-file secure-copy reports plus a master manifest.

Author: Mohit M
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from aive.export.exporter import ExportOptions, FrameRateMode, VideoExporter
from aive.forensics.case import case_store, sha256_file
from aive.forensics.hash_verify import hash_all_algorithms
from aive.forensics.secure_copy import secure_copy
from aive.media.loader import IMAGE_EXTENSIONS, RAW_EXTENSIONS, VIDEO_EXTENSIONS

MANIFEST_NAMES = ("manifest.json", "secure-manifest.json", ".chakshu-manifest.json")

DEFAULT_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | RAW_EXTENSIONS


@dataclass
class SecureMediaFile:
    path: str
    relative_path: str
    size_bytes: int
    sha256: str
    media_type: str
    manifest_verified: bool | None = None


def _classify_media(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in RAW_EXTENSIONS:
        return "raw"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    return "unknown"


def _read_manifest(root: Path) -> dict[str, Any] | None:
    for name in MANIFEST_NAMES:
        manifest = root / name
        if manifest.is_file():
            try:
                return json.loads(manifest.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
    return None


def scan_secure_media(
    root: Path,
    *,
    extensions: set[str] | None = None,
    verify_manifest: bool = True,
) -> dict[str, Any]:
    """Discover media under root (recursive) and compute hashes."""
    root = root.expanduser().resolve()
    if not root.is_dir():
        return {"success": False, "error": f"Not a directory: {root}"}

    ext_set = extensions or DEFAULT_EXTENSIONS
    manifest = _read_manifest(root) if verify_manifest else None
    manifest_hashes: dict[str, str] = {}
    if manifest and isinstance(manifest.get("files"), list):
        for entry in manifest["files"]:
            if isinstance(entry, dict) and entry.get("relative_path") and entry.get("sha256"):
                manifest_hashes[str(entry["relative_path"]).replace("\\", "/")] = str(entry["sha256"])

    files: list[SecureMediaFile] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in ext_set:
            continue
        if path.name in MANIFEST_NAMES:
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        digest = sha256_file(path)
        verified: bool | None = None
        if rel in manifest_hashes:
            verified = manifest_hashes[rel].lower() == digest.lower()
        files.append(
            SecureMediaFile(
                path=str(path),
                relative_path=rel,
                size_bytes=path.stat().st_size,
                sha256=digest,
                media_type=_classify_media(path),
                manifest_verified=verified,
            )
        )

    return {
        "success": True,
        "root": str(root),
        "count": len(files),
        "has_manifest": manifest is not None,
        "files": [asdict(f) for f in files],
    }


def register_secure_media(
    root: Path,
    *,
    actor: str = "examiner",
    case_id: str | None = None,
    extensions: set[str] | None = None,
) -> dict[str, Any]:
    """Register secure-media files in the active case (reference by path, no copy)."""
    scan = scan_secure_media(root, extensions=extensions)
    if not scan.get("success"):
        return scan

    registered: list[dict[str, Any]] = []
    skipped = 0
    for raw in scan["files"]:
        path = Path(raw["path"])
        before = len(case_store.active_case().evidence)
        try:
            item = case_store.register_evidence_reference(
                path,
                actor,
                case_id=case_id,
                relative_path=raw["relative_path"],
                secure_root=scan["root"],
            )
        except FileNotFoundError:
            continue
        after = len(case_store.active_case().evidence)
        if after > before:
            registered.append(
                {
                    "evidence_id": item.evidence_id,
                    "filename": item.filename,
                    "path": str(path),
                    "sha256": item.sha256,
                }
            )
        else:
            skipped += 1

    return {
        "success": True,
        "root": scan["root"],
        "registered": len(registered),
        "skipped": skipped,
        "items": registered,
    }


def batch_secure_export(
    source_root: Path,
    output_dir: Path,
    *,
    mode: str = "copy",
    report_dir: Path | None = None,
    preserve_structure: bool = True,
    extensions: set[str] | None = None,
    use_stream_copy: bool = True,
) -> dict[str, Any]:
    """
    Batch export from secure media.

    mode:
      - copy: verified secure copy (all file types)
      - stream_copy: ffmpeg stream copy for video; secure copy for images
    """
    scan = scan_secure_media(source_root, extensions=extensions)
    if not scan.get("success"):
        return scan

    source_root = Path(scan["root"])
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_root = (report_dir or output_dir / "_secure_reports").expanduser().resolve()
    reports_root.mkdir(parents=True, exist_ok=True)

    exporter = VideoExporter()
    jobs: list[dict[str, Any]] = []
    done = 0
    failed = 0

    for raw in scan["files"]:
        src = Path(raw["path"])
        rel = Path(raw["relative_path"])
        if preserve_structure:
            dst = output_dir / rel
        else:
            dst = output_dir / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        report_path = reports_root / f"{rel.as_posix().replace('/', '__')}.json"

        entry: dict[str, Any] = {
            "source": str(src),
            "destination": str(dst),
            "relative_path": raw["relative_path"],
            "mode": mode,
        }

        try:
            if mode == "stream_copy" and raw["media_type"] == "video":
                opts = ExportOptions(
                    output_path=dst,
                    use_stream_copy=use_stream_copy,
                    frame_rate_mode=FrameRateMode.CFR,
                    faststart=True,
                )
                result = exporter.export(src, opts)
                if not result.get("success"):
                    entry.update({"success": False, "error": result.get("stderr", "Export failed")})
                    failed += 1
                else:
                    post = hash_all_algorithms(dst)
                    verified = post.get("sha256") == raw["sha256"] if use_stream_copy else True
                    entry.update(
                        {
                            "success": True,
                            "verified": verified,
                            "dest_hashes": post,
                            "source_sha256": raw["sha256"],
                        }
                    )
                    report_path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
                    done += 1
            else:
                result = secure_copy(src, dst, report_path)
                if not result.get("success"):
                    entry.update({"success": False, "error": result.get("error", "Copy failed")})
                    failed += 1
                else:
                    entry.update(result)
                    done += 1
        except Exception as e:
            entry.update({"success": False, "error": str(e)})
            failed += 1

        jobs.append(entry)

    master = {
        "timestamp": datetime.utcnow().isoformat(),
        "source_root": str(source_root),
        "output_dir": str(output_dir),
        "mode": mode,
        "preserve_structure": preserve_structure,
        "total": len(jobs),
        "done": done,
        "failed": failed,
        "jobs": jobs,
    }
    master_path = reports_root / "batch-secure-export.json"
    master_path.write_text(json.dumps(master, indent=2), encoding="utf-8")

    return {
        "success": failed == 0,
        "total": len(jobs),
        "done": done,
        "failed": failed,
        "output_dir": str(output_dir),
        "report_path": str(master_path),
        "reports_dir": str(reports_root),
    }
