"""
Secure file copy with hash validation and reporting.

Author: Mohit M
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from aive.forensics.hash_verify import hash_all_algorithms


@dataclass
class CopyReport:
    source: str
    destination: str
    timestamp: str
    size_bytes: int
    source_hashes: dict[str, str]
    dest_hashes: dict[str, str]
    verified: bool


def secure_copy(source: Path, destination: Path, report_path: Path | None = None) -> dict[str, Any]:
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if not source.exists():
        return {"success": False, "error": "Source not found"}

    destination.parent.mkdir(parents=True, exist_ok=True)
    pre_src = hash_all_algorithms(source)
    shutil.copy2(source, destination)
    post_dst = hash_all_algorithms(destination)

    verified = pre_src.get("sha256") == post_dst.get("sha256")
    report = CopyReport(
        source=str(source),
        destination=str(destination),
        timestamp=datetime.utcnow().isoformat(),
        size_bytes=destination.stat().st_size,
        source_hashes=pre_src,
        dest_hashes=post_dst,
        verified=verified,
    )
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")

    return {"success": True, "verified": verified, "report": asdict(report)}
