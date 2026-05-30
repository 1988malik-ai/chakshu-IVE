"""Forensic case management, evidence, and chain of custody."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class CustodyEntry:
    timestamp: str
    action: str
    actor: str
    notes: str = ""
    hash_before: str | None = None
    hash_after: str | None = None


@dataclass
class EvidenceItem:
    evidence_id: str
    filename: str
    media_type: str
    sha256: str
    size_bytes: int
    ingested: str
    source_path: str | None = None
    storage_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    custody: list[CustodyEntry] = field(default_factory=list)


@dataclass
class ForensicCase:
    case_id: str
    case_number: str
    title: str
    examiner: str
    agency: str = ""
    status: str = "open"  # open | active | closed
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    evidence: list[EvidenceItem] = field(default_factory=list)
    notes: str = ""
    tags: list[str] = field(default_factory=list)

    def log_custody(self, evidence_id: str, action: str, actor: str, notes: str = "", **kwargs: str) -> None:
        for ev in self.evidence:
            if ev.evidence_id == evidence_id:
                ev.custody.append(
                    CustodyEntry(
                        timestamp=datetime.utcnow().isoformat(),
                        action=action,
                        actor=actor,
                        notes=notes,
                        hash_before=kwargs.get("hash_before"),
                        hash_after=kwargs.get("hash_after"),
                    )
                )
                self.updated = datetime.utcnow().isoformat()
                return
        raise KeyError(f"Evidence not found: {evidence_id}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CaseStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path.home() / ".ai-ive" / "cases"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._cases: dict[str, ForensicCase] = {}
        self._active_case_id: str | None = None

    def create_case(self, case_number: str, title: str, examiner: str, agency: str = "") -> ForensicCase:
        case = ForensicCase(
            case_id=str(uuid.uuid4()),
            case_number=case_number,
            title=title,
            examiner=examiner,
            agency=agency,
        )
        self._cases[case.case_id] = case
        self._active_case_id = case.case_id
        self._persist(case)
        return case

    def active_case(self) -> ForensicCase:
        if self._active_case_id and self._active_case_id in self._cases:
            return self._cases[self._active_case_id]
        if self._cases:
            self._active_case_id = next(iter(self._cases))
            return self._cases[self._active_case_id]
        c = self.create_case("CASE-001", "New Examination", "Examiner")
        return c

    def set_active(self, case_id: str) -> ForensicCase:
        if case_id not in self._cases:
            raise KeyError(case_id)
        self._active_case_id = case_id
        return self._cases[case_id]

    def list_cases(self) -> list[ForensicCase]:
        self._load_all()
        return list(self._cases.values())

    def add_evidence_from_bytes(
        self,
        case_id: str,
        data: bytes,
        filename: str,
        media_type: str,
        actor: str,
    ) -> EvidenceItem:
        case = self._cases.get(case_id) or self.active_case()
        digest = sha256_bytes(data)
        ev_dir = self.base_dir / case.case_id / "evidence"
        ev_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{digest[:12]}_{filename}"
        storage = ev_dir / safe_name
        storage.write_bytes(data)

        item = EvidenceItem(
            evidence_id=str(uuid.uuid4()),
            filename=filename,
            media_type=media_type,
            sha256=digest,
            size_bytes=len(data),
            ingested=datetime.utcnow().isoformat(),
            storage_path=str(storage),
            metadata={},
        )
        item.custody.append(
            CustodyEntry(
                timestamp=item.ingested,
                action="INGEST",
                actor=actor,
                notes=f"SHA-256: {digest}",
                hash_after=digest,
            )
        )
        case.evidence.append(item)
        case.updated = datetime.utcnow().isoformat()
        self._persist(case)
        return item

    def _persist(self, case: ForensicCase) -> None:
        path = self.base_dir / case.case_id / "case.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "case_id": case.case_id,
            "case_number": case.case_number,
            "title": case.title,
            "examiner": case.examiner,
            "agency": case.agency,
            "status": case.status,
            "created": case.created,
            "updated": case.updated,
            "notes": case.notes,
            "tags": case.tags,
            "evidence": [
                {
                    **{k: v for k, v in asdict(ev).items() if k != "custody"},
                    "custody": [asdict(c) for c in ev.custody],
                }
                for ev in case.evidence
            ],
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load_all(self) -> None:
        for case_dir in self.base_dir.iterdir():
            if not case_dir.is_dir():
                continue
            meta = case_dir / "case.json"
            if not meta.exists():
                continue
            raw = json.loads(meta.read_text())
            evidence = []
            for ev in raw.get("evidence", []):
                custody = [CustodyEntry(**c) for c in ev.pop("custody", [])]
                evidence.append(EvidenceItem(**ev, custody=custody))
            case = ForensicCase(
                evidence=evidence,
                **{k: raw[k] for k in ForensicCase.__dataclass_fields__ if k != "evidence" and k in raw},
            )
            self._cases[case.case_id] = case


case_store = CaseStore()
