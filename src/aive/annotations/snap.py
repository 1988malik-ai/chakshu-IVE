"""Snap points to grid and image guides."""

from __future__ import annotations


def snap_value(v: float, step: float) -> float:
    if step <= 0:
        return v
    return round(v / step) * step


def snap_point(
    x: float,
    y: float,
    width: int,
    height: int,
    grid: int = 10,
    snap_center: bool = True,
    snap_edges: bool = True,
) -> tuple[float, float]:
    sx, sy = snap_value(x, grid), snap_value(y, grid)
    if snap_center:
        cx, cy = width / 2, height / 2
        if abs(x - cx) <= grid:
            sx = cx
        if abs(y - cy) <= grid:
            sy = cy
    if snap_edges:
        for edge_x in (0, width):
            if abs(x - edge_x) <= grid:
                sx = float(edge_x)
        for edge_y in (0, height):
            if abs(y - edge_y) <= grid:
                sy = float(edge_y)
    return sx, sy
