"""R-157 multi-image perspective alignment.

Align one or more target images into a reference image plane using either
manual point correspondences or automatic ORB feature matching.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from aive.imaging import HAS_CV2, bgr_from_bytes, save_bgr_jpeg

if HAS_CV2:
    import cv2
else:  # pragma: no cover - exercised in environments without OpenCV
    cv2 = None  # type: ignore


Point = tuple[float, float]


@dataclass
class AlignmentCorrespondence:
    input_path: str
    reference_points: list[Point] = field(default_factory=list)
    moving_points: list[Point] = field(default_factory=list)


def _load_bgr(path: Path) -> np.ndarray:
    return bgr_from_bytes(path.read_bytes(), path.name)


def _as_points(raw: list[Any]) -> np.ndarray:
    pts: list[list[float]] = []
    for item in raw:
        if isinstance(item, dict):
            pts.append([float(item["x"]), float(item["y"])])
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            pts.append([float(item[0]), float(item[1])])
    return np.asarray(pts, dtype=np.float32)


def _manual_homography(
    reference_points: list[Any],
    moving_points: list[Any],
) -> tuple[np.ndarray, int, float]:
    ref = _as_points(reference_points)
    mov = _as_points(moving_points)
    if len(ref) < 4 or len(mov) < 4:
        raise ValueError("Manual alignment needs at least four reference and moving points")
    if len(ref) != len(mov):
        raise ValueError("Reference and moving point counts must match")
    h, mask = cv2.findHomography(mov, ref, cv2.RANSAC, 3.0)
    if h is None:
        raise ValueError("Could not solve manual homography")
    projected = cv2.perspectiveTransform(mov.reshape(-1, 1, 2), h).reshape(-1, 2)
    rms = float(np.sqrt(np.mean(np.sum((projected - ref) ** 2, axis=1))))
    inliers = int(mask.sum()) if mask is not None else len(ref)
    return h, inliers, rms


def _auto_homography(
    reference: np.ndarray,
    moving: np.ndarray,
    *,
    max_features: int,
    min_matches: int,
) -> tuple[np.ndarray, int, float]:
    gray_ref = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    gray_mov = cv2.cvtColor(moving, cv2.COLOR_BGR2GRAY)
    orb = cv2.ORB_create(nfeatures=max(128, int(max_features)))
    kp_ref, des_ref = orb.detectAndCompute(gray_ref, None)
    kp_mov, des_mov = orb.detectAndCompute(gray_mov, None)
    if des_ref is None or des_mov is None or len(kp_ref) < 4 or len(kp_mov) < 4:
        raise ValueError("Not enough features for automatic alignment")
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    pairs = matcher.knnMatch(des_mov, des_ref, k=2)
    good = []
    for pair in pairs:
        if len(pair) < 2:
            continue
        m, n = pair
        if n is not None and m.distance < 0.75 * n.distance:
            good.append(m)
    if len(good) < max(4, int(min_matches)):
        raise ValueError(f"Only {len(good)} feature matches; need {min_matches}")
    mov_pts = np.float32([kp_mov[m.queryIdx].pt for m in good])
    ref_pts = np.float32([kp_ref[m.trainIdx].pt for m in good])
    h, mask = cv2.findHomography(mov_pts, ref_pts, cv2.RANSAC, 4.0)
    if h is None:
        raise ValueError("Could not solve automatic homography")
    inlier_mask = mask.ravel().astype(bool) if mask is not None else np.ones(len(good), dtype=bool)
    projected = cv2.perspectiveTransform(mov_pts[inlier_mask].reshape(-1, 1, 2), h).reshape(-1, 2)
    rms = float(np.sqrt(np.mean(np.sum((projected - ref_pts[inlier_mask]) ** 2, axis=1))))
    return h, int(inlier_mask.sum()), rms


def _correspondence_for(
    input_path: Path,
    correspondences: list[AlignmentCorrespondence],
) -> AlignmentCorrespondence | None:
    candidates = {str(input_path), input_path.name, input_path.stem}
    for c in correspondences:
        raw = str(c.input_path)
        if raw in candidates or Path(raw).expanduser() == input_path:
            return c
    return None


def align_image_set(
    reference_path: Path,
    input_paths: list[Path],
    output_dir: Path,
    *,
    method: str = "auto",
    correspondences: list[AlignmentCorrespondence] | None = None,
    max_features: int = 2500,
    min_matches: int = 18,
    quality: int = 92,
) -> dict[str, Any]:
    """Align each input image to the reference image geometry."""
    if not HAS_CV2:
        return {"success": False, "outputs": [], "errors": ["OpenCV is required for perspective alignment"]}
    if not input_paths:
        return {"success": False, "outputs": [], "errors": ["At least one target image is required"]}

    output_dir.mkdir(parents=True, exist_ok=True)
    reference = _load_bgr(reference_path)
    out_h, out_w = reference.shape[:2]
    manual = [c for c in (correspondences or []) if c]
    outputs: list[dict[str, Any]] = []
    errors: list[str] = []

    for idx, input_path in enumerate(input_paths, start=1):
        try:
            moving = _load_bgr(input_path)
            corr = _correspondence_for(input_path, manual)
            if method == "manual" or corr is not None:
                if corr is None:
                    raise ValueError(f"No manual correspondence points supplied for {input_path.name}")
                matrix, inliers, rms = _manual_homography(corr.reference_points, corr.moving_points)
                mode = "manual"
            else:
                matrix, inliers, rms = _auto_homography(
                    reference,
                    moving,
                    max_features=max_features,
                    min_matches=min_matches,
                )
                mode = "auto"
            aligned = cv2.warpPerspective(
                moving,
                matrix,
                (out_w, out_h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REPLICATE,
            )
            out_path = output_dir / f"{input_path.stem}_aligned_{idx:02d}.jpg"
            save_bgr_jpeg(out_path, aligned, quality=quality)
            outputs.append(
                {
                    "input_path": str(input_path),
                    "output_path": str(out_path),
                    "method": mode,
                    "width": int(out_w),
                    "height": int(out_h),
                    "inliers": int(inliers),
                    "rms_error_px": round(float(rms), 3),
                    "homography": [[round(float(v), 8) for v in row] for row in matrix.tolist()],
                }
            )
        except Exception as exc:
            errors.append(f"{input_path.name}: {exc}")

    manifest = {
        "success": bool(outputs),
        "reference_path": str(reference_path),
        "output_dir": str(output_dir),
        "method": method,
        "outputs": outputs,
        "errors": errors,
    }
    manifest_path = output_dir / "alignment_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest
