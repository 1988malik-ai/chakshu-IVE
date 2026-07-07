import math

from aive.measurement.tools import Calibration, estimate_speed, measure_distance
from aive.annotations.media_id import canonical_media_id
from aive.measurement.store import MeasurementStore


def test_measure_distance_includes_uncertainty_breakdown():
    result = measure_distance(
        (0, 0),
        (30, 40),
        Calibration(
            pixels_per_unit=10,
            unit_name="cm",
            point_uncertainty_px=0.5,
            calibration_uncertainty_percent=2,
            perspective_uncertainty_percent=1,
        ),
    )

    assert result["distance_px"] == 50
    assert result["distance"] == 5
    assert result["unit"] == "cm"
    assert result["uncertainty_breakdown"]["method"] == "root-sum-square"
    assert result["uncertainty_breakdown"]["pointing_px"] == 0.5
    expected = math.sqrt(0.05**2 + 0.1**2 + 0.05**2)
    assert result["uncertainty"] == expected
    assert result["uncertainty_px"] == expected * 10


def test_estimate_speed_propagates_distance_uncertainty():
    result = estimate_speed(
        (0, 0),
        (0, 20),
        2,
        Calibration(pixels_per_unit=10, unit_name="cm", point_uncertainty_px=1),
    )

    assert result["speed"] == 1
    assert result["unit"] == "cm/s"
    assert result["uncertainty"] == 0.05


def test_measurement_store_uses_canonical_video_path_ids(tmp_path):
    store = MeasurementStore(tmp_path / "measurements.json")
    raw_media_id = "/Users/example/cases/CHK-1/evidence/video.mp4"
    canonical = canonical_media_id(raw_media_id)

    store.add(canonical, 12, [0, 0], [10, 0], {"distance": 10, "unit": "px"})

    assert len(store.list(canonical_media_id(raw_media_id))) == 1
