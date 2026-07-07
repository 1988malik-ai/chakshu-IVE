"""
Image measurement tools with calibration.

Author: Mohit M
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class Calibration:
    pixels_per_unit: float = 1.0
    unit_name: str = "px"
    point_uncertainty_px: float = 0.5
    calibration_uncertainty_percent: float = 0.0
    perspective_uncertainty_percent: float = 0.0


def measure_distance(p1: tuple[float, float], p2: tuple[float, float], cal: Calibration) -> dict[str, Any]:
    px = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    pixels_per_unit = cal.pixels_per_unit if cal.pixels_per_unit > 0 else 1.0
    units = px / pixels_per_unit
    point_uncertainty_px = max(cal.point_uncertainty_px, 0.0)
    point_uncertainty_units = point_uncertainty_px / pixels_per_unit
    calibration_uncertainty_units = units * max(cal.calibration_uncertainty_percent, 0.0) / 100.0
    perspective_uncertainty_units = units * max(cal.perspective_uncertainty_percent, 0.0) / 100.0
    uncertainty_units = math.sqrt(
        point_uncertainty_units**2
        + calibration_uncertainty_units**2
        + perspective_uncertainty_units**2
    )
    relative_uncertainty = uncertainty_units / units if units else 0.0
    return {
        "distance_px": px,
        "distance": units,
        "unit": cal.unit_name,
        "uncertainty": uncertainty_units,
        "uncertainty_px": uncertainty_units * pixels_per_unit,
        "relative_uncertainty": relative_uncertainty,
        "uncertainty_breakdown": {
            "pointing_px": point_uncertainty_px,
            "pointing": point_uncertainty_units,
            "calibration": calibration_uncertainty_units,
            "perspective": perspective_uncertainty_units,
            "method": "root-sum-square",
        },
        "uncertainty_note": (
            "Combined estimate from endpoint picking, calibration, and perspective terms "
            "(root-sum-square)."
        ),
    }


def estimate_speed(
    p1: tuple[float, float],
    p2: tuple[float, float],
    delta_time_sec: float,
    cal: Calibration,
) -> dict[str, Any]:
    dist = measure_distance(p1, p2, cal)
    if delta_time_sec <= 0:
        return {"error": "invalid time delta"}
    speed = dist["distance"] / delta_time_sec
    rel_unc = (dist["uncertainty"] / dist["distance"]) if dist["distance"] else 1.0
    return {
        "speed": speed,
        "unit": f"{cal.unit_name}/s",
        "uncertainty": speed * rel_unc,
        "delta_time_sec": delta_time_sec,
    }
