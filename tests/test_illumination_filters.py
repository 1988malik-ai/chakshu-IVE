"""Illumination filter smoke tests."""

from __future__ import annotations

import numpy as np
import pytest

from aive.filters.catalog import get_filter
from aive.filters.forensic_ops import apply_catalog_filter
from aive.filters.illumination import apply_illumination_filter
from aive.imaging import HAS_CV2


@pytest.mark.skipif(not HAS_CV2, reason="OpenCV required")
def test_homomorphic_filter_runs():
    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    frame[16:48, 16:48] = 200
    out = apply_illumination_filter(frame, "ill_homomorphic", {"sigma": 10, "order": 0.5})
    assert out is not None
    assert out.shape == frame.shape


@pytest.mark.skipif(not HAS_CV2, reason="OpenCV required")
def test_illumination_filters_in_catalog():
    for fid in (
        "ill_homomorphic",
        "ill_retinex",
        "ill_adaptive_flatten",
        "ill_clahe_luminance",
        "ill_shadow_lift",
    ):
        spec = get_filter(fid)
        assert spec is not None
        assert spec.category.value == "illumination"


@pytest.mark.skipif(not HAS_CV2, reason="OpenCV required")
def test_catalog_homomorphic_via_apply():
    frame = np.full((32, 32, 3), 120, dtype=np.uint8)
    out = apply_catalog_filter(frame, "ill_homomorphic", {"sigma": 8})
    assert out.shape == frame.shape
