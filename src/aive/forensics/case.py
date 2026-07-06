"""Forensic case management, evidence, and chain of custody."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

CASE_NUMBER_PREFIX = "CHK"
_GENERIC_CASE_NUMBERS = frozenset({"", "CASE-001", "NEW", "NEW CASE"})


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

    @property
    def display_id(self) -> str:
        """Human-readable identifier for UI and reports."""
        if self.case_number and self.case_number.upper() not in _GENERIC_CASE_NUMBERS:
            return self.case_number
        if self.case_id and not _looks_like_uuid(self.case_id):
            return self.case_id
        return self.case_number or self.case_id

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


def _looks_like_uuid(value: str) -> bool:
    v = value.replace("-", "")
    return len(v) == 32 and all(c in "0123456789abcdefABCDEF" for c in v)


def _slug_case_id(case_number: str) -> str:
    s = case_number.strip().upper()
    s = re.sub(r"[^\w\-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return (s[:48] if s else "") or f"{CASE_NUMBER_PREFIX}-{datetime.utcnow().strftime('%Y%m%d')}"


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

    def _next_case_number(self) -> str:
        """CHK-YYYYMMDD-001 style — date + daily sequence."""
        self._load_all()
        today = datetime.utcnow().strftime("%Y%m%d")
        prefix = f"{CASE_NUMBER_PREFIX}-{today}-"
        nums: list[int] = []
        for case in self._cases.values():
            for candidate in (case.case_number, case.case_id):
                if not candidate or not candidate.startswith(prefix):
                    continue
                tail = candidate[len(prefix) :]
                if tail.isdigit():
                    nums.append(int(tail))
        seq = max(nums, default=0) + 1
        return f"{prefix}{seq:03d}"

    def _unique_case_id(self, base: str) -> str:
        if base not in self._cases:
            return base
        for i in range(2, 1000):
            candidate = f"{base}-{i:02d}"
            if candidate not in self._cases:
                return candidate
        return f"{base}-{uuid.uuid4().hex[:6].upper()}"

    def _allocate_case_ids(self, case_number: str = "") -> tuple[str, str]:
        requested = (case_number or "").strip()
        if not requested or requested.upper() in _GENERIC_CASE_NUMBERS:
            number = self._next_case_number()
        else:
            number = requested.upper()
        case_id = self._unique_case_id(_slug_case_id(number))
        return case_id, number

    def _next_evidence_id(self, case: ForensicCase) -> str:
        nums: list[int] = []
        for ev in case.evidence:
            if ev.evidence_id.startswith("EV-"):
                tail = ev.evidence_id[3:]
                if tail.isdigit():
                    nums.append(int(tail))
        return f"EV-{max(nums, default=0) + 1:03d}"

    def create_case(
        self,
        case_number: str = "",
        title: str = "New Examination",
        examiner: str = "Examiner",
        agency: str = "",
    ) -> ForensicCase:
        case_id, number = self._allocate_case_ids(case_number)
        case = ForensicCase(
            case_id=case_id,
            case_number=number,
            title=title,
            examiner=examiner,
            agency=agency,
        )
        self._cases[case.case_id] = case
        self._active_case_id = case.case_id
        self._persist(case)
        return case

    def _upgrade_display_number(self, case: ForensicCase) -> None:
        """Replace generic CASE-001 with a readable Chakshu case number."""
        if case.case_number.strip().upper() not in _GENERIC_CASE_NUMBERS:
            return
        case.case_number = self._next_case_number()
        self._persist(case)

    def active_case(self) -> ForensicCase:
        self._load_all()
        if self._active_case_id and self._active_case_id in self._cases:
            case = self._cases[self._active_case_id]
            self._upgrade_display_number(case)
            return case
        if self._cases:
            self._active_case_id = next(iter(self._cases))
            case = self._cases[self._active_case_id]
            self._upgrade_display_number(case)
            return case
        c = self.create_case(title="New Examination", examiner="Examiner")
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
            evidence_id=self._next_evidence_id(case),
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

    def register_evidence_reference(
        self,
        path: Path,
        actor: str,
        *,
        case_id: str | None = None,
        relative_path: str = "",
        secure_root: str = "",
    ) -> EvidenceItem:
        """Register evidence by filesystem path (secure media — no byte copy)."""
        case = self._cases.get(case_id) if case_id else self.active_case()
        if case is None:
            case = self.active_case()
        path = path.expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)

        digest = sha256_file(path)
        for ev in case.evidence:
            if ev.sha256 == digest or ev.storage_path == str(path):
                return ev

        ext = path.suffix.lower()
        if ext in {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".mxf", ".ts", ".m4v", ".mpg", ".mpeg"}:
            media_type = "video"
        elif ext in {".cr2", ".nef", ".arw", ".dng", ".orf", ".rw2", ".raf", ".pef"}:
            media_type = "raw"
        else:
            media_type = "image"

        item = EvidenceItem(
            evidence_id=self._next_evidence_id(case),
            filename=path.name,
            media_type=media_type,
            sha256=digest,
            size_bytes=path.stat().st_size,
            ingested=datetime.utcnow().isoformat(),
            source_path=str(path),
            storage_path=str(path),
            metadata={
                "secure_media": True,
                "secure_media_root": secure_root,
                "relative_path": relative_path or path.name,
            },
        )
        item.custody.append(
            CustodyEntry(
                timestamp=item.ingested,
                action="SECURE_MEDIA_LOAD",
                actor=actor,
                notes=f"Referenced from secure media: {relative_path or path.name}",
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
