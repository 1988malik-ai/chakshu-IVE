from pathlib import Path

import numpy as np
import pytest

from aive.imaging import HAS_CV2, save_bgr_jpeg
from aive.panorama import (
    convert_omnidirectional,
    convert_omnidirectional_file,
    equirectangular_to_rectilinear,
    fisheye_to_equirectangular,
)


pytestmark = pytest.mark.skipif(not HAS_CV2, reason="OpenCV required")


def _synthetic_equirectangular(width: int = 256, height: int = 128) -> np.ndarray:
    x = np.linspace(0, 255, width, dtype=np.uint8)
    y = np.linspace(0, 255, height, dtype=np.uint8)
    xx, yy = np.meshgrid(x, y)
    return np.dstack([xx, yy, np.full_like(xx, 90)])


def test_equirectangular_to_rectilinear_uses_view_controls():
    frame = _synthetic_equirectangular()

    front = equirectangular_to_rectilinear(
        frame,
        yaw_deg=0,
        pitch_deg=0,
        roll_deg=0,
        out_width=96,
        out_height=64,
    )
    side = equirectangular_to_rectilinear(
        frame,
        yaw_deg=90,
        pitch_deg=0,
        roll_deg=15,
        out_width=96,
        out_height=64,
    )

    assert front.shape == (64, 96, 3)
    assert side.shape == (64, 96, 3)
    assert np.mean(np.abs(front.astype(np.int16) - side.astype(np.int16))) > 5


def test_fisheye_to_equirectangular_outputs_two_to_one_panorama():
    frame = np.zeros((120, 120, 3), dtype=np.uint8)
    yy, xx = np.ogrid[:120, :120]
    mask = (xx - 60) ** 2 + (yy - 60) ** 2 <= 55 ** 2
    frame[mask] = (80, 160, 240)

    out = fisheye_to_equirectangular(frame, fov_deg=180, out_width=240, out_height=120)

    assert out.shape == (120, 240, 3)
    assert out.mean() > 10


def test_convert_omnidirectional_file_writes_panorama_jpeg(tmp_path: Path):
    source = tmp_path / "source.jpg"
    output = tmp_path / "panorama.jpg"
    save_bgr_jpeg(source, _synthetic_equirectangular())

    result = convert_omnidirectional_file(
        source,
        output,
        source_type="equirectangular",
        output_type="rectilinear",
        yaw_deg=45,
        pitch_deg=10,
        roll_deg=5,
        out_width=128,
        out_height=96,
    )

    assert result["success"] is True
    assert result["width"] == 128
    assert result["height"] == 96
    assert output.exists()
    assert output.stat().st_size > 0


def test_convert_omnidirectional_supports_cylindrical_output():
    frame = _synthetic_equirectangular()

    out = convert_omnidirectional(
        frame,
        source_type="equirectangular",
        output_type="cylindrical",
        out_width=200,
        out_height=100,
    )

    assert out.shape == (100, 200, 3)
