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


def measure_distance(p1: tuple[float, float], p2: tuple[float, float], cal: Calibration) -> dict[str, Any]:
    px = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    units = px / cal.pixels_per_unit if cal.pixels_per_unit else px
    uncertainty_px = 0.5
    uncertainty_units = uncertainty_px / cal.pixels_per_unit if cal.pixels_per_unit else uncertainty_px
    return {
        "distance_px": px,
        "distance": units,
        "unit": cal.unit_name,
        "uncertainty": uncertainty_units,
        "uncertainty_note": "±0.5 px instrumental minimum",
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
