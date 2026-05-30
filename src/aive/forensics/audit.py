"""Append-only forensic audit log."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class AuditEvent:
    timestamp: str
    case_id: str
    event_type: str
    actor: str
    detail: dict[str, Any]


class AuditLog:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / ".ai-ive" / "audit.log.jsonl"

    def record(self, case_id: str, event_type: str, actor: str, **detail: Any) -> AuditEvent:
        ev = AuditEvent(
            timestamp=datetime.utcnow().isoformat(),
            case_id=case_id,
            event_type=event_type,
            actor=actor,
            detail=detail,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(ev)) + "\n")
        return ev

    def list_for_case(self, case_id: str, limit: int = 200) -> list[AuditEvent]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            if raw.get("case_id") == case_id:
                out.append(AuditEvent(**raw))
        return out[-limit:]


audit_log = AuditLog()
