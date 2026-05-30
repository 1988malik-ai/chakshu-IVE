"""Forensic enhancement filters — Phase 4 full catalog dispatch."""

from __future__ import annotations

from typing import Any

import numpy as np

from aive.filters.catalog import FILTER_CATALOG
from aive.filters.forensic_ops import apply_catalog_filter
from aive.imaging import apply_basic_filter

# All catalog filters are live in Phase 4
FORENSIC_FILTER_IDS = frozenset(f.id for f in FILTER_CATALOG)

# Legacy forensic-only ids (not in catalog)
_EXTRA_FORENSIC = frozenset({
    "frn_noise_profile",
    "frn_shadow_lift",
    "frn_highlight_recover",
})


def apply_forensic_filter(frame: np.ndarray, fid: str, p: dict[str, Any] | None = None) -> np.ndarray:
    params = p or {}
    if fid in _EXTRA_FORENSIC or fid in FORENSIC_FILTER_IDS:
        return apply_catalog_filter(frame, fid, params)
    return apply_basic_filter(frame, fid, params)
