"""Filter processing engine — applies catalog filters to frames."""

from __future__ import annotations

from typing import Any

import numpy as np

from aive.filters.catalog import get_filter
from aive.filters.forensic import apply_forensic_filter
from aive.filters.forensic import FORENSIC_FILTER_IDS as _CATALOG_IDS


def apply_filter(frame: np.ndarray, filter_id: str, params: dict[str, Any] | None = None) -> np.ndarray:
    spec = get_filter(filter_id)
    if spec is None:
        raise ValueError(f"Unknown filter: {filter_id}")
    p = {**spec.params, **(params or {})}
    return apply_forensic_filter(frame, filter_id, p)


def is_implemented(filter_id: str) -> bool:
    """Phase 4: every catalog filter is executable."""
    return get_filter(filter_id) is not None


def build_filter_chain(specs: list[tuple[str, dict[str, Any] | None]]) -> CallableChain:
    return CallableChain(specs)


class CallableChain:
    def __init__(self, specs: list[tuple[str, dict[str, Any] | None]]) -> None:
        self._specs = specs

    def apply(self, frame: np.ndarray) -> np.ndarray:
        out = frame
        for fid, params in self._specs:
            out = apply_filter(out, fid, params)
        return out


def implemented_count() -> int:
    return len(_CATALOG_IDS)
