"""
Illumination adjustment filters — homomorphic, Retinex, CLAHE, adaptive flatten.

Forensic use: uneven lighting, shadow recovery, backlit scenes, CCTV glare.

Author: Mohit M
"""

from __future__ import annotations

from typing import Any

import numpy as np

from aive.imaging import HAS_CV2

if HAS_CV2:
    import cv2


def _clip_u8(arr: np.ndarray) -> np.ndarray:
    return np.clip(arr, 0, 255).astype(np.uint8)


def homomorphic_filter(frame: np.ndarray, sigma: float = 30.0, order: float = 0.5) -> np.ndarray:
    """R-153 — separate illumination (low-freq) from reflectance in log domain."""
    if not HAS_CV2:
        return frame
    img = frame.astype(np.float32) + 1.0
    log_img = np.log(img)
    blur = cv2.GaussianBlur(log_img, (0, 0), max(float(sigma), 1.0))
    illum = log_img - float(order) * blur
    out = np.exp(illum) - 1.0
    return _clip_u8(out)


def multi_scale_retinex(
    frame: np.ndarray,
    scales: tuple[float, ...] | list[float] = (15.0, 80.0, 250.0),
    gain: float = 1.0,
) -> np.ndarray:
    """MSR — balance shadows and highlights by comparing to multi-scale Gaussian envelopes."""
    if not HAS_CV2:
        return frame
    img = frame.astype(np.float32) + 1.0
    retinex = np.zeros_like(img, dtype=np.float32)
    scale_list = [float(s) for s in scales] or [15.0, 80.0, 250.0]
    for sigma in scale_list:
        blur = cv2.GaussianBlur(img, (0, 0), max(sigma, 1.0))
        retinex += np.log(img) - np.log(blur + 1.0)
    retinex /= len(scale_list)
    out = retinex * float(gain)
    for c in range(3):
        ch = out[:, :, c]
        lo, hi = float(ch.min()), float(ch.max())
        out[:, :, c] = (ch - lo) / max(hi - lo, 1e-6) * 255.0
    return _clip_u8(out)


def adaptive_illumination_flatten(frame: np.ndarray, sigma: float = 40.0) -> np.ndarray:
    """Divide L-channel by blurred luminance estimate to flatten uneven lighting."""
    if not HAS_CV2:
        return frame
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)
    lum = lab[:, :, 0] + 1.0
    illum = cv2.GaussianBlur(lum, (0, 0), max(float(sigma), 1.0))
    lab[:, :, 0] = np.clip((lum / np.maximum(illum, 1.0)) * 128.0, 0, 255)
    return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)


def clahe_luminance(frame: np.ndarray, clip: float = 2.0) -> np.ndarray:
    """CLAHE on L channel — local illumination / contrast normalization."""
    if not HAS_CV2:
        return frame
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=max(float(clip), 0.1), tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def shadow_lift(frame: np.ndarray, amount: float = 0.35) -> np.ndarray:
    """Lift dark regions (shadows) while limiting highlight blow-out."""
    if not HAS_CV2:
        return frame
    amt = float(np.clip(amount, 0.0, 1.0))
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)
    shadow = lab[:, :, 0] < 110
    lab[:, :, 0][shadow] = np.clip(lab[:, :, 0][shadow] * (1.0 + amt * 0.35) + amt * 18, 0, 255)
    return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)


def apply_illumination_filter(
    frame: np.ndarray,
    filter_id: str,
    params: dict[str, Any] | None = None,
) -> np.ndarray | None:
    """Dispatch ill_* and illumination-related catalog ids."""
    if not HAS_CV2:
        return None
    p = params or {}
    fid = filter_id

    if fid in ("ill_homomorphic", "adv_homomorphic") or fid.startswith("ill_homomorph"):
        return homomorphic_filter(
            frame,
            float(p.get("sigma", 30.0)),
            float(p.get("order", 0.5)),
        )
    if fid in ("ill_retinex", "ill_msr") or fid.startswith("ill_retinex"):
        scales = p.get("scales", (15.0, 80.0, 250.0))
        if isinstance(scales, str):
            scales = tuple(float(x) for x in scales.split(",") if x.strip())
        return multi_scale_retinex(frame, scales, float(p.get("gain", 1.0)))
    if fid in ("ill_adaptive_flatten", "ill_flatten") or fid.startswith("ill_adaptive"):
        return adaptive_illumination_flatten(frame, float(p.get("sigma", 40.0)))
    if fid in ("ill_clahe", "ill_clahe_luminance") or fid.startswith("ill_clahe"):
        return clahe_luminance(frame, float(p.get("clip", 2.0)))
    if fid in ("ill_shadow_lift", "frn_shadow_lift") or fid.startswith("ill_shadow"):
        return shadow_lift(frame, float(p.get("amount", p.get("strength", 0.35))))

    return None
