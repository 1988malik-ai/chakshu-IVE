"""R-172 — stream sync and frame similarity."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from aive.imaging import HAS_CV2
from aive.video.seek import extract_frame_bgr

if HAS_CV2:
    import cv2


def _gray(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 3:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return frame


def frame_similarity(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    """Histogram + MSE similarity between two BGR frames (same size)."""
    if not HAS_CV2:
        return {"score": 0.0, "method": "opencv_missing"}
    if a.shape != b.shape:
        b = cv2.resize(b, (a.shape[1], a.shape[0]))
    ga, gb = _gray(a), _gray(b)
    mse = float(np.mean((ga.astype(np.float32) - gb.astype(np.float32)) ** 2))
    hist_a = cv2.calcHist([ga], [0], None, [64], [0, 256])
    hist_b = cv2.calcHist([gb], [0], None, [64], [0, 256])
    cv2.normalize(hist_a, hist_a)
    cv2.normalize(hist_b, hist_b)
    hist_corr = float(cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL))
    score = max(0.0, min(1.0, hist_corr * (1.0 - min(mse / 65025.0, 1.0))))
    return {
        "score": round(score, 4),
        "hist_correlation": round(hist_corr, 4),
        "mse": round(mse, 2),
        "method": "histogram+mse",
    }


def compare_streams_at_time(
    path_a: Path,
    path_b: Path,
    time_a: float,
    time_b: float,
) -> dict[str, Any]:
    fa = extract_frame_bgr(path_a, time_a)
    fb = extract_frame_bgr(path_b, time_b)
    if fa is None or fb is None:
        return {"success": False, "error": "Could not extract frames at given times"}
    sim = frame_similarity(fa, fb)
    return {
        "success": True,
        "time_a": time_a,
        "time_b": time_b,
        "similarity": sim,
        "sync_hint_ms": round((time_b - time_a) * 1000, 1),
    }


def find_best_offset(
    path_a: Path,
    path_b: Path,
    center_time_a: float = 0.0,
    search_sec: float = 2.0,
    step_sec: float = 0.25,
) -> dict[str, Any]:
    """Search ±search_sec on stream B for best visual match to frame at center_time_a on A."""
    fa = extract_frame_bgr(path_a, center_time_a)
    if fa is None:
        return {"success": False, "error": "Could not extract reference frame from A"}

    best = {"score": -1.0, "time_b": 0.0}
    t = max(0.0, center_time_a - search_sec)
    end = center_time_a + search_sec
    samples = []
    while t <= end:
        fb = extract_frame_bgr(path_b, t)
        if fb is not None:
            sim = frame_similarity(fa, fb)
            samples.append({"time_b": t, **sim})
            if sim["score"] > best["score"]:
                best = {"score": sim["score"], "time_b": t}
        t += step_sec

    offset_ms = round((best["time_b"] - center_time_a) * 1000, 1)
    return {
        "success": True,
        "reference_time_a": center_time_a,
        "best_match_time_b": best["time_b"],
        "best_score": best["score"],
        "recommended_offset_ms": offset_ms,
        "samples": samples,
    }
