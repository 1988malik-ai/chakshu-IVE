from pathlib import Path

import numpy as np
import pytest

from aive.comparison.session import compare_store
from aive.imaging import HAS_CV2, save_bgr_jpeg
from aive.overlays.compose import draw_pip, side_by_side


pytestmark = pytest.mark.skipif(not HAS_CV2, reason="OpenCV required")


def test_side_by_side_composes_two_frames():
    left = np.zeros((40, 60, 3), dtype=np.uint8)
    right = np.full((40, 60, 3), 255, dtype=np.uint8)

    combined = side_by_side(left, right)

    assert combined.shape == (40, 120, 3)
    assert combined[:, :60].mean() == 0
    assert combined[:, 60:].mean() == 255


def test_picture_in_picture_changes_selected_corner():
    background = np.zeros((100, 140, 3), dtype=np.uint8)
    inset = np.full((40, 40, 3), 200, dtype=np.uint8)

    combined = draw_pip(background, inset, scale=0.5, position="bottom-right", margin=5)

    assert combined.shape == background.shape
    assert combined[75:95, 115:135].mean() > 100
    assert combined[0:20, 0:20].mean() == 0


def test_compare_session_exports_side_by_side_jpeg(tmp_path: Path):
    left_path = tmp_path / "left.jpg"
    right_path = tmp_path / "right.jpg"
    output_path = tmp_path / "compare.jpg"
    save_bgr_jpeg(left_path, np.zeros((32, 48, 3), dtype=np.uint8))
    save_bgr_jpeg(right_path, np.full((32, 48, 3), 180, dtype=np.uint8))

    session = compare_store.create(left_path, right_path)
    result = compare_store.export_image(session.id, output_path, mode="side_by_side")

    assert result["success"] is True
    assert result["width"] == 96
    assert result["height"] == 32
    assert output_path.exists()
    assert output_path.stat().st_size > 0
