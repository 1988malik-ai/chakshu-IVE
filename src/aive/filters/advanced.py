"""
Section 16 — advanced image processing (R-150–R-167).

Homomorphic illumination, deinterlace, deblur, JPEG de-artifact, channel ops,
lens correction, super-resolution, and perspective stabilization previews.

Author: Mohit M
"""

from __future__ import annotations

from typing import Any

import numpy as np

from aive.imaging import HAS_CV2, denoise_colored

if HAS_CV2:
    import cv2


def _clip_u8(arr: np.ndarray) -> np.ndarray:
    return np.clip(arr, 0, 255).astype(np.uint8)


def _gray(frame: np.ndarray) -> np.ndarray:
    if HAS_CV2:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return frame.mean(axis=2).astype(np.uint8)


def _to_bgr(gray: np.ndarray) -> np.ndarray:
    if HAS_CV2:
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return np.stack([gray, gray, gray], axis=-1)


def deinterlace(frame: np.ndarray, mode: str = "bob") -> np.ndarray:
    """R-150 — convert interlaced fields to progressive (bob / weave)."""
    if not HAS_CV2:
        return frame
    h = frame.shape[0]
    if h < 4:
        return frame
    out = frame.copy()
    if mode == "weave":
        even = frame[0::2].copy()
        odd = frame[1::2].copy()
        out[0::2] = cv2.addWeighted(even, 0.5, odd, 0.5, 0)
        out[1::2] = out[0::2]
    else:
        even = frame[0::2]
        odd = frame[1::2]
        blended_even = cv2.addWeighted(even, 0.5, odd, 0.5, 0)
        blended_odd = cv2.addWeighted(odd, 0.5, even, 0.5, 0)
        out[0::2] = blended_even
        out[1::2] = blended_odd
    return out


def interlace_fields(frame: np.ndarray, field: str = "top") -> np.ndarray:
    """R-150 — simulate interlaced output from progressive frame."""
    if not HAS_CV2:
        return frame
    out = frame.copy()
    if field == "bottom":
        out[0::2] = frame[1::2]
    else:
        out[1::2] = frame[0::2]
    return out


def homomorphic_filter(frame: np.ndarray, sigma: float = 30.0, order: float = 0.5) -> np.ndarray:
    """R-153 — illumination normalization in log-frequency domain."""
    from aive.filters.illumination import homomorphic_filter as _homomorphic

    return _homomorphic(frame, sigma, order)


def auto_contrast_halo_suppress(frame: np.ndarray, clip: float = 2.5) -> np.ndarray:
    """R-154 — CLAHE auto contrast with bilateral halo suppression."""
    if not HAS_CV2:
        return frame
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    smooth = cv2.bilateralFilter(enhanced, 9, 75, 75)
    detail = cv2.addWeighted(enhanced, 1.35, smooth, -0.35, 0)
    return cv2.bilateralFilter(_clip_u8(detail), 5, 40, 40)


def color_channel_isolate(frame: np.ndarray, channel: str = "r") -> np.ndarray:
    """R-155 — isolate or emphasize a color component."""
    if not HAS_CV2:
        return frame
    ch = channel.lower()
    b, g, r = cv2.split(frame)
    if ch in ("r", "red"):
        return cv2.merge([np.zeros_like(b), np.zeros_like(g), r])
    if ch in ("g", "green"):
        return cv2.merge([np.zeros_like(b), g, np.zeros_like(r)])
    if ch in ("b", "blue"):
        return cv2.merge([b, np.zeros_like(g), np.zeros_like(r)])
    if ch in ("c", "cyan"):
        inv = 255 - r
        return cv2.merge([inv, inv, np.zeros_like(b)])
    if ch in ("m", "magenta"):
        inv = 255 - g
        return cv2.merge([inv, np.zeros_like(g), inv])
    if ch in ("y", "yellow"):
        inv = 255 - b
        return cv2.merge([np.zeros_like(b), inv, inv])
    return cv2.merge([b, g, r])


def motion_deblur(frame: np.ndarray, strength: float = 0.6, angle: float = 0.0) -> np.ndarray:
    """R-156 — edge-preserving motion / defocus deblur (Wiener-style kernel)."""
    if not HAS_CV2:
        return frame
    ksize = max(5, int(9 * strength)) | 1
    rad = np.deg2rad(angle)
    kernel = np.zeros((ksize, ksize), np.float32)
    cx = cy = ksize // 2
    for i in range(ksize):
        x = int(cx + (i - cx) * np.cos(rad))
        y = int(cy + (i - cy) * np.sin(rad))
        if 0 <= x < ksize and 0 <= y < ksize:
            kernel[y, x] = 1.0
    kernel /= max(kernel.sum(), 1e-6)
    inv = np.eye(ksize, dtype=np.float32) + strength * kernel
    try:
        deconv = cv2.filter2D(frame, -1, inv / inv.sum())
    except cv2.error:
        deconv = frame
    sharp = cv2.addWeighted(frame, 1.0 + strength, cv2.GaussianBlur(frame, (0, 0), 2), -strength, 0)
    return cv2.bilateralFilter(_clip_u8(cv2.addWeighted(deconv, 0.55, sharp, 0.45, 0)), 7, 50, 50)


def jpeg_artifact_reduce(frame: np.ndarray, strength: float = 0.6) -> np.ndarray:
    """R-166 — reduce blockiness from JPEG compression."""
    if not HAS_CV2:
        return frame
    h, w = frame.shape[:2]
    denoised = denoise_colored(frame, 4, 4, 7, 21)
    block = 8
    mask = np.zeros((h, w), np.float32)
    for y in range(0, h, block):
        for x in range(0, w, block):
            patch = _gray(frame[y : y + block, x : x + block])
            if patch.size:
                mask[y : y + block, x : x + block] = float(np.std(patch)) / 64.0
    mask = cv2.GaussianBlur(mask, (0, 0), 1.5)
    mask = np.clip(mask * strength, 0, 1)[..., np.newaxis]
    blended = frame.astype(np.float32) * (1 - mask) + denoised.astype(np.float32) * mask
    return cv2.bilateralFilter(_clip_u8(blended), 5, 35, 35)


def channel_invert_replace(
    frame: np.ndarray,
    channel: str = "g",
    mode: str = "invert",
    source: str = "r",
) -> np.ndarray:
    """R-167 — invert or replace individual BGR channels."""
    if not HAS_CV2:
        return frame
    idx = {"b": 0, "g": 1, "r": 2}
    ci = idx.get(channel.lower()[:1], 1)
    si = idx.get(source.lower()[:1], 0)
    out = frame.copy()
    if mode == "invert":
        out[:, :, ci] = 255 - out[:, :, ci]
    elif mode == "zero":
        out[:, :, ci] = 0
    elif mode == "max":
        out[:, :, ci] = 255
    elif mode == "copy":
        out[:, :, ci] = frame[:, :, si]
    elif mode == "swap":
        out[:, :, ci], out[:, :, si] = frame[:, :, si].copy(), frame[:, :, ci].copy()
    return out


def lens_distortion_correct(frame: np.ndarray, k1: float = -0.0006, k2: float = 0.0) -> np.ndarray:
    """R-151 — barrel / pincushion correction via undistort."""
    if not HAS_CV2:
        return frame
    h, w = frame.shape[:2]
    focal = max(w, h)
    cam = np.array([[focal, 0, w / 2], [0, focal, h / 2], [0, 0, 1]], dtype=np.float64)
    dist = np.array([k1, k2, 0, 0, 0], dtype=np.float64)
    return cv2.undistort(frame, cam, dist)


def _parse_corners(raw: Any, w: int, h: int) -> np.ndarray | None:
    if not raw or not isinstance(raw, (list, tuple)) or len(raw) < 4:
        return None
    pts: list[list[float]] = []
    for pt in raw[:4]:
        if isinstance(pt, (list, tuple)) and len(pt) >= 2:
            pts.append([float(pt[0]), float(pt[1])])
    if len(pts) < 4:
        return None
    return np.float32(pts)


def correct_perspective_homography(
    frame: np.ndarray,
    src_corners: list[list[float]] | list[tuple[float, float]],
    dst_corners: list[list[float]] | list[tuple[float, float]] | None = None,
) -> np.ndarray:
    """Map a source quadrilateral to a destination rectangle (keystone / perspective correction)."""
    if not HAS_CV2:
        return frame
    h, w = frame.shape[:2]
    src = _parse_corners(src_corners, w, h)
    if src is None:
        return frame
    if dst_corners:
        dst = _parse_corners(dst_corners, w, h)
    else:
        dst = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
    if dst is None:
        dst = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
    m = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(
        frame,
        m,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )


def perspective_stabilize_preview(frame: np.ndarray) -> np.ndarray:
    """R-158 — single-frame perspective straightening from dominant lines."""
    if not HAS_CV2:
        return frame
    h, w = frame.shape[:2]
    edges = cv2.Canny(_gray(frame), 60, 180)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, max(w // 4, 80))
    if lines is None:
        return frame
    angles = []
    for rho_theta in lines[:12]:
        rho, theta = rho_theta[0]
        ang = (theta * 180 / np.pi) - 90
        if abs(ang) < 25:
            angles.append(ang)
    if not angles:
        return frame
    angle = float(np.median(angles))
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(frame, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def super_resolution(frame: np.ndarray, scale: float = 2.0) -> np.ndarray:
    """R-159 — edge-aware upscale + detail recovery."""
    if not HAS_CV2:
        return frame
    h, w = frame.shape[:2]
    nh, nw = int(h * scale), int(w * scale)
    up = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_CUBIC)
    blur = cv2.GaussianBlur(up, (0, 0), 1.2)
    detail = cv2.addWeighted(up, 1.4, blur, -0.4, 0)
    return cv2.bilateralFilter(_clip_u8(detail), 5, 40, 40)


def panoramic_cylindrical(frame: np.ndarray, fov_deg: float = 100.0) -> np.ndarray:
    """R-152 — cylindrical unwrap preview for wide / fisheye-like frames."""
    from aive.panorama import cylindrical_from_wide

    if not HAS_CV2:
        return frame
    return cylindrical_from_wide(frame, fov_deg)


def omnidirectional_panorama(frame: np.ndarray, params: dict[str, Any] | None = None) -> np.ndarray:
    """R-152 — omnidirectional / 360° → panoramic conversion."""
    from aive.panorama import convert_omnidirectional

    if not HAS_CV2:
        return frame
    p = params or {}
    return convert_omnidirectional(
        frame,
        source_type=str(p.get("source_type", "fisheye")),
        output_type=str(p.get("output_type", "equirectangular")),
        fov_deg=float(p.get("fov_deg", p.get("fov", 180))),
        fisheye_model=str(p.get("fisheye_model", "equidistant")),  # type: ignore[arg-type]
        yaw_deg=float(p.get("yaw_deg", 0)),
        pitch_deg=float(p.get("pitch_deg", 0)),
        roll_deg=float(p.get("roll_deg", 0)),
        fov_h_deg=float(p.get("fov_h_deg", 90)),
        fov_v_deg=float(p.get("fov_v_deg", 60)),
        out_width=int(p["out_width"]) if p.get("out_width") else None,
        out_height=int(p["out_height"]) if p.get("out_height") else None,
        cx=float(p["cx"]) if p.get("cx") is not None else None,
        cy=float(p["cy"]) if p.get("cy") is not None else None,
    )


def apply_advanced_filter(frame: np.ndarray, filter_id: str, params: dict[str, Any] | None = None) -> np.ndarray | None:
    """Dispatch advanced Section 16 filters by catalog id or adv_* alias."""
    if not HAS_CV2:
        return None
    p = params or {}
    fid = filter_id

    if fid.startswith("vid_deinterlace") or fid.startswith("both_interlace_fix") or fid == "adv_deinterlace":
        return deinterlace(frame, str(p.get("mode", "bob")))
    if fid == "adv_interlace":
        return interlace_fields(frame, str(p.get("field", "top")))
    if fid.startswith("adv_homomorph") or fid == "adv_homomorphic":
        from aive.filters.illumination import homomorphic_filter as _homomorphic

        return _homomorphic(frame, float(p.get("sigma", 30)), float(p.get("order", 0.5)))
    if fid.startswith("clr_dehaze") and float(p.get("strength", 0)) >= 0.8:
        return homomorphic_filter(frame, float(p.get("sigma", 25)))
    if fid.startswith("both_auto_contrast") or fid == "adv_auto_contrast":
        return auto_contrast_halo_suppress(frame, float(p.get("clip", 2.5)))
    if fid.startswith("adv_channel_replace") or (fid.startswith("clr_channel") and p.get("mode")):
        return channel_invert_replace(
            frame,
            str(p.get("channel", "g")),
            str(p.get("mode", "invert")),
            str(p.get("source", "r")),
        )
    if fid.startswith("clr_channel_mixer") or fid == "adv_color_separate":
        return color_channel_isolate(frame, str(p.get("channel", "r")))
    if fid.startswith("both_deblur_ai") or fid.startswith("adv_deblur") or fid.startswith("adv_motion_deblur"):
        return motion_deblur(frame, float(p.get("strength", 0.6)), float(p.get("angle", 0)))
    if fid.startswith("adv_jpeg") or fid.startswith("rst_jpeg"):
        return jpeg_artifact_reduce(frame, float(p.get("strength", 0.6)))
    if fid.startswith("clr_invert") and p.get("channel"):
        return channel_invert_replace(frame, str(p["channel"]), "invert")
    if fid.startswith("geo_lens") or fid.startswith("geo_barrel") or fid.startswith("geo_pincushion") or fid.startswith("both_lens_correction"):
        k1 = float(p.get("k1", -0.0006 if "barrel" in fid else 0.0006))
        return lens_distortion_correct(frame, k1, float(p.get("k2", 0)))
    if fid.startswith("geo_perspective") or fid.startswith("geo_keystone") or fid.startswith("both_perspective_match"):
        if p.get("src_corners"):
            return correct_perspective_homography(frame, p["src_corners"], p.get("dst_corners"))
        return None
    if fid.startswith("both_perspective") or fid.startswith("adv_perspective") or fid.startswith("both_warp_stabilize"):
        return perspective_stabilize_preview(frame)
    if fid.startswith("rst_super_resolution") or fid.startswith("both_upscale_ai") or fid == "adv_super_resolution":
        return super_resolution(frame, float(p.get("scale", 2)))
    if fid.startswith("adv_panoramic") or fid == "adv_panorama":
        return panoramic_cylindrical(frame, float(p.get("fov", 100)))
    if fid.startswith("adv_omni") or fid == "adv_omnidirectional":
        return omnidirectional_panorama(frame, p)
    if fid.startswith("vid_stabilize") or fid.startswith("both_tracking_stabilize"):
        return perspective_stabilize_preview(_to_bgr(_gray(frame))) if frame.ndim == 2 else perspective_stabilize_preview(frame)

    return None
