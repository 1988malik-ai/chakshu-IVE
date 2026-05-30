"""Optional operation and system information logging."""

from __future__ import annotations

import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class OperationLogger:
    def __init__(self, enabled: bool = False, log_path: Path | None = None) -> None:
        self.enabled = enabled
        self.log_path = log_path or Path("logs/aive_operations.log")
        if self.enabled:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_system_info()

    def log_system_info(self) -> None:
        info = {
            "platform": platform.platform(),
            "python": sys.version,
            "machine": platform.machine(),
            "processor": platform.processor(),
        }
        self._write("SYSTEM", str(info))

    def log(self, operation: str, details: str = "", **kwargs: Any) -> None:
        if not self.enabled:
            return
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{details} {extra}".strip()
        self._write(operation, msg)

    def _write(self, operation: str, message: str) -> None:
        ts = datetime.utcnow().isoformat()
        line = f"[{ts}] [{operation}] {message}\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line)
