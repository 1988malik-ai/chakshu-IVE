from pathlib import Path

import numpy as np
import pytest

from aive.imaging import HAS_CV2, save_bgr_jpeg
from aive.perspective_alignment import AlignmentCorrespondence, align_image_set


pytestmark = pytest.mark.skipif(not HAS_CV2, reason="OpenCV required")

if HAS_CV2:
    import cv2


def _reference_image(width: int = 180, height: int = 130) -> np.ndarray:
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (28, 34, 42)
    for x in range(20, width, 30):
        cv2.line(img, (x, 8), (x, height - 8), (70, 130, 220), 1)
    for y in range(20, height, 24):
        cv2.line(img, (8, y), (width - 8, y), (70, 180, 120), 1)
    cv2.rectangle(img, (35, 28), (145, 98), (240, 220, 80), 2)
    cv2.circle(img, (62, 55), 12, (220, 80, 100), -1)
    cv2.putText(img, "A1", (96, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (230, 230, 230), 2)
    return img


def test_manual_multi_image_alignment_writes_outputs_and_manifest(tmp_path: Path):
    reference = _reference_image()
    ref_path = tmp_path / "reference.jpg"
    moving_path = tmp_path / "moving.jpg"
    output_dir = tmp_path / "aligned"

    reference_points = np.float32([[20, 15], [160, 18], [152, 115], [24, 108]])
    moving_points = np.float32([[8, 24], [168, 8], [158, 122], [36, 118]])
    h = cv2.getPerspectiveTransform(reference_points, moving_points)
    moving = cv2.warpPerspective(reference, h, (reference.shape[1], reference.shape[0]))
    save_bgr_jpeg(ref_path, reference)
    save_bgr_jpeg(moving_path, moving)

    result = align_image_set(
        ref_path,
        [moving_path],
        output_dir,
        method="manual",
        correspondences=[
            AlignmentCorrespondence(
                input_path=str(moving_path),
                reference_points=[tuple(p) for p in reference_points.tolist()],
                moving_points=[tuple(p) for p in moving_points.tolist()],
            )
        ],
    )

    assert result["success"] is True
    assert result["manifest_path"].endswith("alignment_manifest.json")
    assert Path(result["manifest_path"]).exists()
    assert len(result["outputs"]) == 1
    output = result["outputs"][0]
    assert output["method"] == "manual"
    assert output["width"] == reference.shape[1]
    assert output["height"] == reference.shape[0]
    assert output["rms_error_px"] < 0.1
    assert Path(output["output_path"]).exists()


def test_manual_alignment_reports_missing_points(tmp_path: Path):
    ref_path = tmp_path / "reference.jpg"
    moving_path = tmp_path / "moving.jpg"
    output_dir = tmp_path / "aligned"
    save_bgr_jpeg(ref_path, _reference_image())
    save_bgr_jpeg(moving_path, _reference_image())

    result = align_image_set(
        ref_path,
        [moving_path],
        output_dir,
        method="manual",
        correspondences=[],
    )

    assert result["success"] is False
    assert "No manual correspondence" in result["errors"][0]
    assert Path(result["manifest_path"]).exists()
