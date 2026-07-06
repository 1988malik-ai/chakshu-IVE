"""
Panoramic image conversion from omnidirectional sources.

Supports fisheye / 360° equirectangular inputs and converts to equirectangular,
cylindrical panorama, or rectilinear (perspective) views.

Author: Mohit M
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import numpy as np

from aive.imaging import HAS_CV2, bgr_to_jpeg_base64, save_bgr_jpeg

if HAS_CV2:
    import cv2

SourceType = Literal["fisheye", "equirectangular", "omnidirectional"]
OutputType = Literal["equirectangular", "cylindrical", "rectilinear"]
FisheyeModel = Literal["equidistant", "equisolid", "stereographic"]


def _require_cv2() -> None:
    if not HAS_CV2:
        raise RuntimeError("OpenCV required for panoramic conversion (pip install opencv-python-headless)")


def _rotation_yaw_pitch(yaw_deg: float, pitch_deg: float) -> np.ndarray:
    yaw = np.deg2rad(yaw_deg)
    pitch = np.deg2rad(pitch_deg)
    cy, sy = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float64)
    rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]], dtype=np.float64)
    return ry @ rx


def _lonlat_to_equirect_maps(
    lon: np.ndarray,
    lat: np.ndarray,
    src_w: int,
    src_h: int,
) -> tuple[np.ndarray, np.ndarray]:
    map_x = ((lon / (2 * np.pi) + 0.5) * (src_w - 1)).astype(np.float32)
    map_y = ((0.5 - lat / np.pi) * (src_h - 1)).astype(np.float32)
    return map_x, map_y


def fisheye_to_equirectangular(
    frame: np.ndarray,
    *,
    fov_deg: float = 180.0,
    model: FisheyeModel = "equidistant",
    out_width: int | None = None,
    out_height: int | None = None,
    cx: float | None = None,
    cy: float | None = None,
) -> np.ndarray:
    """Unwrap circular fisheye / omnidirectional lens to 2:1 equirectangular."""
    _require_cv2()
    h, w = frame.shape[:2]
    out_w = int(out_width or max(w * 2, 512))
    out_h = int(out_height or max(h, 256))
    cx = float(cx if cx is not None else w / 2)
    cy = float(cy if cy is not None else h / 2)
    r_max = max(8.0, min(cx, cy, w - cx, h - cy) * 0.98)
    fov_rad = np.deg2rad(max(40.0, min(float(fov_deg), 220.0)))

    lon = np.linspace(-np.pi, np.pi, out_w, dtype=np.float64)
    lat = np.linspace(np.pi / 2, -np.pi / 2, out_h, dtype=np.float64)
    lon_g, lat_g = np.meshgrid(lon, lat)

    x = np.cos(lat_g) * np.sin(lon_g)
    y = np.sin(lat_g)
    z = np.cos(lat_g) * np.cos(lon_g)

    theta = np.arccos(np.clip(z, -1.0, 1.0))
    phi = np.arctan2(y, x)

    half_fov = fov_rad / 2
    if model == "equisolid":
        r = 2 * np.sin(theta / 2) / max(np.sin(half_fov / 2), 1e-6) * r_max
    elif model == "stereographic":
        r = 2 * np.tan(theta / 2) / max(np.tan(half_fov / 2), 1e-6) * r_max
    else:
        r = theta / max(half_fov, 1e-6) * r_max

    map_x = (cx + r * np.cos(phi)).astype(np.float32)
    map_y = (cy + r * np.sin(phi)).astype(np.float32)

    valid = (theta <= half_fov + 0.02) & (z >= -0.05)
    out = cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    out[~valid] = 0
    return out


def equirectangular_to_cylindrical(
    frame: np.ndarray,
    *,
    out_width: int | None = None,
    out_height: int | None = None,
) -> np.ndarray:
    """Map 360° equirectangular image to a cylindrical panorama."""
    _require_cv2()
    h, w = frame.shape[:2]
    out_w = int(out_width or w)
    out_h = int(out_height or h)

    lon = np.linspace(-np.pi, np.pi, out_w, dtype=np.float64)
    lat_lin = np.linspace(np.pi / 2, -np.pi / 2, out_h, dtype=np.float64)
    lon_g, lat_g = np.meshgrid(lon, lat_lin)
    map_x, map_y = _lonlat_to_equirect_maps(lon_g, lat_g, w, h)
    return cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def equirectangular_to_rectilinear(
    frame: np.ndarray,
    *,
    yaw_deg: float = 0.0,
    pitch_deg: float = 0.0,
    fov_h_deg: float = 90.0,
    fov_v_deg: float = 60.0,
    out_width: int | None = None,
    out_height: int | None = None,
) -> np.ndarray:
    """Extract a rectilinear perspective view from an equirectangular source."""
    _require_cv2()
    h, w = frame.shape[:2]
    out_w = int(out_width or max(w // 2, 320))
    out_h = int(out_height or max(h // 2, 240))
    fov_h = np.deg2rad(max(20.0, min(float(fov_h_deg), 160.0)))
    fov_v = np.deg2rad(max(20.0, min(float(fov_v_deg), 160.0)))

    u = np.linspace(-1, 1, out_w, dtype=np.float64)
    v = np.linspace(1, -1, out_h, dtype=np.float64)
    u_g, v_g = np.meshgrid(u, v)

    tan_h = np.tan(fov_h / 2)
    tan_v = np.tan(fov_v / 2)
    dirs = np.stack([u_g * tan_h, v_g * tan_v, np.ones_like(u_g)], axis=-1)
    dirs /= np.linalg.norm(dirs, axis=-1, keepdims=True)

    rot = _rotation_yaw_pitch(yaw_deg, pitch_deg)
    world = dirs @ rot.T
    lon = np.arctan2(world[..., 0], world[..., 2])
    lat = np.arcsin(np.clip(world[..., 1], -1.0, 1.0))
    map_x, map_y = _lonlat_to_equirect_maps(lon, lat, w, h)
    return cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def cylindrical_from_wide(frame: np.ndarray, fov_deg: float = 100.0) -> np.ndarray:
    """Cylindrical unwrap for wide / mild fisheye frames (legacy R-152)."""
    _require_cv2()
    h, w = frame.shape[:2]
    fov = np.deg2rad(max(40.0, min(float(fov_deg), 170.0)))
    f = w / fov
    cx, cy = w / 2, h / 2
    x_out = np.arange(w, dtype=np.float64)
    y_out = np.arange(h, dtype=np.float64)
    x_g, y_g = np.meshgrid(x_out, y_out)
    theta = (x_g - cx) / f
    h_off = (y_g - cy) / np.maximum(np.cos(theta), 0.15)
    map_x = np.clip(cx + f * np.tan(theta), 0, w - 1).astype(np.float32)
    map_y = np.clip(cy + h_off, 0, h - 1).astype(np.float32)
    return cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def convert_omnidirectional(
    frame: np.ndarray,
    *,
    source_type: SourceType = "fisheye",
    output_type: OutputType = "equirectangular",
    fov_deg: float = 180.0,
    fisheye_model: FisheyeModel = "equidistant",
    yaw_deg: float = 0.0,
    pitch_deg: float = 0.0,
    fov_h_deg: float = 90.0,
    fov_v_deg: float = 60.0,
    out_width: int | None = None,
    out_height: int | None = None,
    cx: float | None = None,
    cy: float | None = None,
) -> np.ndarray:
    """Convert omnidirectional / 360° source to a panoramic or perspective image."""
    src = source_type.lower().strip()
    out = output_type.lower().strip()

    if src in ("omnidirectional", "fisheye"):
        eq = fisheye_to_equirectangular(
            frame,
            fov_deg=fov_deg,
            model=fisheye_model,
            out_width=out_width,
            out_height=out_height,
            cx=cx,
            cy=cy,
        )
        if out == "equirectangular":
            return eq
        if out == "cylindrical":
            return equirectangular_to_cylindrical(eq, out_width=out_width, out_height=out_height)
        return equirectangular_to_rectilinear(
            eq,
            yaw_deg=yaw_deg,
            pitch_deg=pitch_deg,
            fov_h_deg=fov_h_deg,
            fov_v_deg=fov_v_deg,
            out_width=out_width,
            out_height=out_height,
        )

    if src == "equirectangular":
        if out == "equirectangular":
            return frame
        if out == "cylindrical":
            return equirectangular_to_cylindrical(frame, out_width=out_width, out_height=out_height)
        if out == "rectilinear":
            return equirectangular_to_rectilinear(
                frame,
                yaw_deg=yaw_deg,
                pitch_deg=pitch_deg,
                fov_h_deg=fov_h_deg,
                fov_v_deg=fov_v_deg,
                out_width=out_width,
                out_height=out_height,
            )

    if out == "cylindrical" and src == "wide":
        return cylindrical_from_wide(frame, fov_deg)

    raise ValueError(f"Unsupported conversion: {source_type} → {output_type}")


def convert_omnidirectional_file(
    input_path: Path,
    output_path: Path,
    **kwargs: Any,
) -> dict[str, Any]:
    """Load image, convert, and save panoramic output."""
    _require_cv2()
    inp = input_path.expanduser().resolve()
    out = output_path.expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    if not inp.is_file():
        return {"success": False, "error": f"Not found: {inp}"}

    frame = cv2.imread(str(inp), cv2.IMREAD_COLOR)
    if frame is None:
        from aive.imaging import bgr_from_bytes

        frame = bgr_from_bytes(inp.read_bytes(), inp.name)

    result = convert_omnidirectional(frame, **kwargs)
    save_bgr_jpeg(out, result)
    return {
        "success": True,
        "output_path": str(out),
        "width": int(result.shape[1]),
        "height": int(result.shape[0]),
        "source_type": kwargs.get("source_type", "fisheye"),
        "output_type": kwargs.get("output_type", "equirectangular"),
    }


def panorama_preview_base64(frame: np.ndarray, **kwargs: Any) -> dict[str, Any]:
    """Convert frame and return JPEG preview metadata."""
    out = convert_omnidirectional(frame, **kwargs)
    return {
        "preview": bgr_to_jpeg_base64(out),
        "width": int(out.shape[1]),
        "height": int(out.shape[0]),
    }
