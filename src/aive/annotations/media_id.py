"""Canonical media keys for annotation storage (evidence id vs storage path)."""

from __future__ import annotations

from pathlib import Path


def canonical_media_id(media_id: str) -> str:
    """Resolve evidence UUID or path alias to a stable storage-path key."""
    raw = (media_id or "").strip()
    if not raw:
        return raw

    try:
        from aive.forensics.case import case_store

        case = case_store.active_case()
        for ev in case.evidence:
            sp = str(Path(ev.storage_path).expanduser().resolve())
            if raw == ev.evidence_id or raw == ev.storage_path:
                return sp
            try:
                if Path(raw).expanduser().resolve() == Path(ev.storage_path).expanduser().resolve():
                    return sp
            except OSError:
                pass
    except Exception:
        pass

    try:
        p = Path(raw).expanduser()
        if p.exists():
            return str(p.resolve())
    except OSError:
        pass

    return raw


def media_id_aliases(media_id: str) -> set[str]:
    """All keys that may hold annotations for this media."""
    keys: set[str] = {media_id.strip()} if media_id else set()
    canon = canonical_media_id(media_id)
    if canon:
        keys.add(canon)
    try:
        from aive.forensics.case import case_store

        case = case_store.active_case()
        for ev in case.evidence:
            sp = str(Path(ev.storage_path).expanduser().resolve())
            if canon == sp or media_id in (ev.evidence_id, ev.storage_path):
                keys.add(ev.evidence_id)
                keys.add(ev.storage_path)
                keys.add(sp)
    except Exception:
        pass
    return {k for k in keys if k}
