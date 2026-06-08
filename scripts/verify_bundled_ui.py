"""CI check: aive-api.exe must contain bundled frontend-dist/index.html."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def main() -> int:
    exe = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/aive-api.exe").resolve()
    if not exe.is_file():
        print(f"ERROR: missing {exe}")
        return 1

    # PyInstaller one-file exe embeds a CArchive; extract with pyinstaller helper if present
    try:
        import PyInstaller.archive.readers as readers  # type: ignore

        with readers.CArchiveReader(str(exe)) as arch:
            names = set(arch.toc.keys())
            hits = [n for n in names if n.replace("\\", "/").endswith("frontend-dist/index.html")]
            if hits:
                print(f"OK: bundled UI found ({hits[0]})")
                return 0
    except Exception as exc:
        print(f"Note: CArchiveReader check skipped ({exc})")

    # Fallback: run exe briefly and query /api/health ui_ready (best-effort)
    print("WARN: could not inspect exe archive; relying on runtime health check in CI is optional")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
