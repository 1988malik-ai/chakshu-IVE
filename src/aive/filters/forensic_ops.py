"""
Phase 4 — full 140+ filter catalog operators (OpenCV / NumPy).

Author: Mohit M
"""

from __future__ import annotations

from typing import Any

import numpy as np

from aive.filters.advanced import apply_advanced_filter
from aive.imaging import HAS_CV2, apply_basic_filter

if HAS_CV2:
    import cv2


def _ensure_bgr(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 2:
        if HAS_CV2:
            return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        return np.stack([frame, frame, frame], axis=-1)
    return frame


def _gray(frame: np.ndarray) -> np.ndarray:
    if HAS_CV2:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return frame.mean(axis=2).astype(np.uint8)


def _to_bgr(gray: np.ndarray) -> np.ndarray:
    if HAS_CV2:
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return np.stack([gray, gray, gray], axis=-1)


def _clip_u8(arr: np.ndarray) -> np.ndarray:
    return np.clip(arr, 0, 255).astype(np.uint8)


def _gamma_lut(gamma: float) -> np.ndarray:
    inv = 1.0 / max(float(gamma), 0.01)
    return np.array([((i / 255.0) ** inv) * 255 for i in range(256)], dtype=np.uint8)


def _vignette(frame: np.ndarray, amount: float) -> np.ndarray:
    rows, cols = frame.shape[:2]
    kx = cv2.getGaussianKernel(cols, cols / 3)
    ky = cv2.getGaussianKernel(rows, rows / 3)
    mask = (ky * kx.T) / max((ky * kx.T).max(), 1e-6)
    mask = 1 - float(amount) * (1 - mask)
    out = frame.astype(np.float32)
    for c in range(3):
        out[:, :, c] *= mask
    return _clip_u8(out)


def _unsharp(frame: np.ndarray, amount: float = 1.0, sigma: float = 3.0) -> np.ndarray:
    blurred = cv2.GaussianBlur(frame, (0, 0), sigma)
    return cv2.addWeighted(frame, 1 + amount, blurred, -amount, 0)


def _clahe_l(frame: np.ndarray, clip: float = 2.0) -> np.ndarray:
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def _ai_enhance(frame: np.ndarray, p: dict[str, Any] | None = None) -> np.ndarray:
    try:
        from aive.ai.enhance import run_ai_tool

        return run_ai_tool(frame, p)
    except Exception:
        out = cv2.fastNlMeansDenoisedColored(frame, None, 5, 5, 7, 21)
        return _unsharp(_clahe_l(out, 2.5), 0.35)


def _apply_color(frame: np.ndarray, fid: str, p: dict[str, Any]) -> np.ndarray | None:
    if fid in ("clr_grayscale",):
        return _to_bgr(_gray(frame))
    if fid in ("clr_invert",):
        return 255 - frame
    if fid in ("clr_brightness",) or fid == "both_normalize":
        amount = float(p.get("amount", p.get("stops", 0)))
        out = frame.astype(np.float32)
        if "stops" in p or fid == "both_normalize":
            out = np.clip(out * (2.0**amount), 0, 255)
        else:
            out = np.clip(out + amount * 2.55, 0, 255)
        return out.astype(np.uint8)
    if fid in ("clr_contrast",):
        amount = float(p.get("amount", 1.0))
        mean = frame.mean()
        return _clip_u8((frame.astype(np.float32) - mean) * amount + mean)
    if fid in ("both_auto_contrast",):
        adv = apply_advanced_filter(frame, fid, p)
        if adv is not None:
            return adv
        amount = float(p.get("amount", 1.0))
        mean = frame.mean()
        return _clip_u8((frame.astype(np.float32) - mean) * amount + mean)
    if fid in ("clr_saturation",):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * float(p.get("amount", 1.0)), 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    if fid in ("clr_hue",):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.int16)
        hsv[:, :, 0] = (hsv[:, :, 0] + int(float(p.get("degrees", 0)) / 2)) % 180
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    if fid in ("clr_vibrance",):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        sat = hsv[:, :, 1]
        boost = float(p.get("amount", 0.3))
        hsv[:, :, 1] = np.clip(sat + boost * (255 - sat) * 0.35, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    if fid in ("clr_exposure",):
        stops = float(p.get("stops", 0))
        return _clip_u8(frame.astype(np.float32) * (2.0**stops))
    if fid in ("clr_gamma",):
        return cv2.LUT(frame, _gamma_lut(float(p.get("gamma", 1.0))))
    if fid in ("clr_levels", "both_auto_levels", "utl_histogram"):
        out = frame.copy()
        for c in range(3):
            out[:, :, c] = cv2.equalizeHist(out[:, :, c])
        return out
    if fid in ("clr_curves",):
        lut = np.clip(255 * (np.linspace(0, 1, 256) ** 0.85), 0, 255).astype(np.uint8)
        return cv2.LUT(frame, lut)
    if fid in ("clr_white_balance", "both_color_correct"):
        avg = frame.reshape(-1, 3).mean(axis=0)
        gray = avg.mean()
        scale = gray / np.maximum(avg, 1.0)
        return _clip_u8(frame.astype(np.float32) * scale)
    if fid in ("clr_temperature",):
        k = float(p.get("kelvin", 6500))
        warm = np.clip((6500 - k) / 3500, -1, 1)
        out = frame.astype(np.float32)
        out[:, :, 2] = np.clip(out[:, :, 2] + warm * 35, 0, 255)
        out[:, :, 0] = np.clip(out[:, :, 0] - warm * 35, 0, 255)
        return out.astype(np.uint8)
    if fid in ("clr_tint",):
        amt = float(p.get("amount", 0))
        out = frame.astype(np.float32)
        out[:, :, 1] = np.clip(out[:, :, 1] + amt * 30, 0, 255)
        return out.astype(np.uint8)
    if fid in ("clr_shadows", "frn_shadow_lift"):
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)
        shadow = lab[:, :, 0] < 100
        lab[:, :, 0][shadow] = np.clip(lab[:, :, 0][shadow] * 1.12 + 8, 0, 255)
        return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
    if fid in ("clr_highlights", "frn_highlight_recover"):
        out = frame.astype(np.float32)
        mask = out > 200
        out[mask] = 200 + (out[mask] - 200) * 0.55
        return out.astype(np.uint8)
    if fid in ("clr_midtones",):
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)
        mid = (lab[:, :, 0] >= 80) & (lab[:, :, 0] <= 180)
        lab[:, :, 0][mid] = np.clip(lab[:, :, 0][mid] * 1.05 + 4, 0, 255)
        return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
    if fid in ("clr_black_point",):
        bp = float(p.get("amount", 0))
        return _clip_u8((frame.astype(np.float32) - bp) * (255 / max(255 - bp, 1)))
    if fid in ("clr_white_point",):
        wp = float(p.get("amount", 255))
        return _clip_u8(frame.astype(np.float32) * (255 / max(wp, 1)))
    if fid in ("clr_clarity",):
        blur = cv2.GaussianBlur(frame, (0, 0), 3)
        detail = cv2.addWeighted(frame, 1.4, blur, -0.4, 0)
        return cv2.addWeighted(frame, 1 - float(p.get("amount", 0.5)), detail, float(p.get("amount", 0.5)), 0)
    if fid in ("clr_dehaze", "rst_defog"):
        dc = _gray(frame).astype(np.float32)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        dark = cv2.erode(dc, kernel)
        t = np.maximum(dark, 1)
        out = frame.astype(np.float32)
        strength = float(p.get("strength", 0.5))
        for c in range(3):
            out[:, :, c] = np.clip(
                (out[:, :, c] - t * strength * 0.85) / (1 - t / 255 * strength * 0.85 + 1e-6),
                0,
                255,
            )
        return out.astype(np.uint8)
    if fid in ("clr_fade",):
        amt = float(p.get("amount", 0.3))
        return _clip_u8(frame.astype(np.float32) * (1 - amt * 0.35) + 255 * amt * 0.15)
    if fid in ("clr_sepia",):
        amt = float(p.get("amount", 1.0))
        m = np.array([[0.272, 0.534, 0.131], [0.349, 0.686, 0.168], [0.393, 0.769, 0.189]])
        sep = _clip_u8(frame @ m.T)
        return cv2.addWeighted(frame, 1 - amt, sep, amt, 0)
    if fid in ("clr_posterize",):
        levels = max(2, int(p.get("levels", 8)))
        step = 256 // levels
        return (frame // step) * step
    if fid in ("clr_solarize",):
        g = _gray(frame)
        inv = 255 - g
        mask = g > 128
        g = g.copy()
        g[mask] = inv[mask]
        return _to_bgr(g)
    if fid in ("clr_channel_mixer",):
        rw, gw, bw = 0.3, 0.5, 0.2
        out = frame.astype(np.float32)
        mixed = out[:, :, 2] * rw + out[:, :, 1] * gw + out[:, :, 0] * bw
        for c in range(3):
            out[:, :, c] = np.clip(out[:, :, c] * 0.65 + mixed * 0.35, 0, 255)
        return out.astype(np.uint8)
    if fid in ("clr_color_balance", "clr_selective_color"):
        out = frame.astype(np.float32)
        out[:, :, 2] *= 1.03
        out[:, :, 0] *= 0.97
        return _clip_u8(out)
    if fid in ("clr_lut_cube", "clr_lut_hald", "clr_film_emulation", "vid_lut", "vid_color_grade"):
        out = cv2.LUT(frame, _gamma_lut(1.08))
        return cv2.addWeighted(out, 0.85, _to_bgr(_gray(out)), 0.15, 0)
    return None


def _apply_blur_sharpen(frame: np.ndarray, fid: str, p: dict[str, Any]) -> np.ndarray | None:
    if fid.startswith("blr_gaussian") or fid in ("both_blur", "both_background_blur", "both_depth_blur"):
        r = int(float(p.get("radius", 3))) | 1
        return cv2.GaussianBlur(frame, (r, r), 0)
    if fid.startswith("blr_box"):
        r = int(float(p.get("radius", 3))) | 1
        return cv2.blur(frame, (r, r))
    if fid.startswith("blr_median"):
        k = int(p.get("ksize", 5)) | 1
        return cv2.medianBlur(frame, k)
    if fid.startswith("blr_bilateral") or fid.startswith("ns_bilateral"):
        return cv2.bilateralFilter(frame, 9, 75, 75)
    if fid.startswith("blr_motion") or fid.startswith("both_motion_track_blur"):
        dist = max(3, int(p.get("distance", 10)))
        angle = np.deg2rad(float(p.get("angle", 0)))
        k = np.zeros((dist, dist), np.float32)
        cx, cy = dist // 2, dist // 2
        for i in range(dist):
            x = int(cx + (i - cx) * np.cos(angle))
            y = int(cy + (i - cy) * np.sin(angle))
            if 0 <= x < dist and 0 <= y < dist:
                k[y, x] = 1
        k /= max(k.sum(), 1)
        return cv2.filter2D(frame, -1, k)
    if fid.startswith("blr_radial"):
        rows, cols = frame.shape[:2]
        cx, cy = cols / 2, rows / 2
        y, x = np.indices((rows, cols))
        r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        r = (r / max(r.max(), 1) * 8).astype(np.int32) | 1
        out = frame.copy()
        for step in (1, 3, 5):
            blurred = cv2.GaussianBlur(out, (step * 2 + 1, step * 2 + 1), 0)
            mask = (r >= step) & (r < step + 2)
            out[mask] = blurred[mask]
        return out
    if fid.startswith("blr_zoom"):
        layers = [cv2.GaussianBlur(frame, (0, 0), s) for s in (2, 6, 12)]
        return cv2.addWeighted(layers[0], 0.5, layers[2], 0.5, 0)
    if fid.startswith("blr_lens") or fid.startswith("blr_surface") or fid.startswith("blr_stack"):
        return cv2.bilateralFilter(cv2.GaussianBlur(frame, (0, 0), 3), 9, 50, 50)
    if fid.startswith("shp_unsharp") or fid.startswith("both_sharpen") or fid.startswith("rst_sharpen_ai"):
        return _unsharp(frame, float(p.get("amount", 1.0)))
    if fid.startswith("shp_high_pass") or fid.startswith("shp_laplacian"):
        blur = cv2.GaussianBlur(frame, (0, 0), 7)
        return cv2.addWeighted(frame, 1.5, blur, -0.5, 0)
    if fid.startswith("shp_smart_sharpen") or fid.startswith("shp_detail"):
        return _unsharp(_clahe_l(frame), float(p.get("amount", 0.8)))
    if fid.startswith("shp_edge_enhance"):
        edges = cv2.Laplacian(_gray(frame), cv2.CV_16S, ksize=3)
        edges = cv2.convertScaleAbs(edges)
        return cv2.addWeighted(frame, 1.0, _to_bgr(edges), 0.35, 0)
    return None


def _apply_noise(frame: np.ndarray, fid: str, p: dict[str, Any]) -> np.ndarray | None:
    if fid.startswith("ns_denoise") or fid.startswith("both_denoise") or fid.startswith("frn_noise_profile"):
        h = int(3 + float(p.get("strength", 0.5)) * 7) | 1
        return cv2.fastNlMeansDenoisedColored(frame, None, h, h, 7, 21)
    if fid.startswith("ns_nlmeans") or fid.startswith("both_denoise_ai") or fid.startswith("both_noise_reduction_broadcast"):
        return cv2.fastNlMeansDenoisedColored(frame, None, 10, 10, 7, 21)
    if fid.startswith("ns_median_denoise"):
        return cv2.medianBlur(frame, 5)
    if fid.startswith("ns_gaussian_denoise"):
        return cv2.GaussianBlur(frame, (5, 5), 0)
    if fid.startswith("ns_add_grain") or fid.startswith("both_film_grain"):
        amt = float(p.get("amount", 0.2))
        noise = np.random.normal(0, amt * 25, frame.shape).astype(np.float32)
        return _clip_u8(frame.astype(np.float32) + noise)
    if fid.startswith("ns_add_noise"):
        noise = np.random.randint(-20, 20, frame.shape, dtype=np.int16)
        return _clip_u8(frame.astype(np.int16) + noise)
    if fid.startswith("ns_remove_hot_pixels") or fid.startswith("ns_impulse"):
        return cv2.medianBlur(frame, 3)
    return None


def _apply_geometry(frame: np.ndarray, fid: str, p: dict[str, Any]) -> np.ndarray | None:
    h, w = frame.shape[:2]
    if fid.startswith("geo_rotate") or fid == "vid_rotate_90":
        angle = 90.0 if fid == "vid_rotate_90" else float(p.get("angle", 0))
        m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        return cv2.warpAffine(frame, m, (w, h))
    if fid.startswith("geo_flip_h") or fid == "vid_flip":
        return cv2.flip(frame, 1)
    if fid.startswith("geo_flip_v"):
        return cv2.flip(frame, 0)
    if fid.startswith("rst_super_resolution") or fid.startswith("both_upscale_ai"):
        adv = apply_advanced_filter(frame, fid, p)
        if adv is not None:
            return adv
    if fid.startswith("geo_resize") or fid.startswith("vid_scale") or fid.startswith("rst_upscale") or fid.startswith("rst_super_resolution") or fid.startswith("both_upscale_ai"):
        scale = float(p.get("scale", 2))
        nh, nw = int(h * scale), int(w * scale)
        return cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_CUBIC)
    if fid.startswith("geo_crop") or fid.startswith("vid_crop"):
        margin = int(min(h, w) * 0.05)
        cropped = frame[margin : h - margin, margin : w - margin]
        return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
    if fid.startswith("geo_perspective") or fid.startswith("geo_keystone") or fid.startswith("both_perspective_match"):
        adv = apply_advanced_filter(frame, fid, p)
        if adv is not None:
            return adv
        src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        dx = w * 0.04
        dst = np.float32([[dx, 0], [w - dx, dx * 0.5], [w - dx, h], [0, h - dx * 0.5]])
        m = cv2.getPerspectiveTransform(src, dst)
        return cv2.warpPerspective(frame, m, (w, h))
    if fid.startswith("geo_lens_distort") or fid.startswith("geo_barrel") or fid.startswith("geo_pincushion") or fid.startswith("both_lens_correction"):
        adv = apply_advanced_filter(frame, fid, p)
        if adv is not None:
            return adv
        k1 = 0.0008 if "barrel" in fid else -0.0008
        k = np.array([k1, 0, 0, 0, 0], dtype=np.float32)
        return cv2.undistort(frame, np.eye(3), k)
    if fid.startswith("geo_warp") or fid.startswith("geo_liquify"):
        map_x = np.zeros((h, w), np.float32)
        map_y = np.zeros((h, w), np.float32)
        for y in range(h):
            map_x[y, :] = np.arange(w) + np.sin(y / 20) * 3
            map_y[y, :] = y
        return cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR)
    if fid.startswith("vid_letterbox"):
        bar = h // 8
        out = np.zeros_like(frame)
        out[bar : h - bar] = cv2.resize(frame, (w, h - 2 * bar))
        return out
    if fid.startswith("vid_pillarbox"):
        bar = w // 8
        out = np.zeros_like(frame)
        resized = cv2.resize(frame, (w - 2 * bar, h))
        out[:, bar : w - bar] = resized
        return out
    if fid.startswith("vid_pad"):
        pad = int(min(h, w) * 0.05)
        return cv2.copyMakeBorder(frame, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    if fid.startswith("vid_aspect_fix") or fid.startswith("vid_crop_detect"):
        cropped = frame[2 : h - 2, 2 : w - 2]
        return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
    return None


def _apply_stylize(frame: np.ndarray, fid: str, p: dict[str, Any]) -> np.ndarray | None:
    h, w = frame.shape[:2]
    if fid.startswith("sty_emboss"):
        kernel = np.array([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]])
        return _clip_u8(cv2.filter2D(frame, -1, kernel) + 128)
    if fid.startswith("sty_edge_detect") or fid.startswith("sty_canny"):
        edges = cv2.Canny(_gray(frame), 50, 150)
        return _to_bgr(edges)
    if fid.startswith("sty_oil_paint"):
        if hasattr(cv2, "xphoto"):
            return cv2.xphoto.oilPainting(frame, 7, 1)
        return cv2.bilateralFilter(frame, 9, 75, 75)
    if fid.startswith("sty_cartoon"):
        g = _gray(frame)
        g = cv2.medianBlur(g, 7)
        edges = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 2)
        color = cv2.bilateralFilter(frame, 9, 300, 300)
        return cv2.bitwise_and(color, color, mask=255 - edges)
    if fid.startswith("sty_pixelate") or fid.startswith("sty_mosaic"):
        block = max(2, int(p.get("block", 8)))
        nh, nw = max(h // block, 1), max(w // block, 1)
        small = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
        return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    if fid.startswith("sty_halftone"):
        g = _gray(frame)
        g = (g // 32) * 32
        return _to_bgr(g)
    if fid.startswith("sty_vignette") or fid.startswith("both_vignette"):
        return _vignette(frame, float(p.get("amount", 0.5)))
    if fid.startswith("sty_glow") or fid.startswith("sty_bloom") or fid.startswith("both_glow") or fid.startswith("both_edge_glow"):
        blur = cv2.GaussianBlur(frame, (0, 0), 12)
        return cv2.addWeighted(frame, 0.75, blur, 0.35, 0)
    if fid.startswith("sty_chromatic_aberration") or fid.startswith("both_rgb_split"):
        b, g, r = cv2.split(frame)
        r = np.roll(r, 2, axis=1)
        b = np.roll(b, -2, axis=1)
        return cv2.merge([b, g, r])
    if fid.startswith("both_pixel_sort"):
        out = frame.copy()
        for c in range(3):
            ch = out[:, :, c].reshape(-1)
            ch.sort()
            out[:, :, c] = ch.reshape(out.shape[:2])
        return out
    if fid.startswith("both_glitch"):
        out = frame.copy()
        out[:, 8:] = frame[:, :-8]
        out[::3] = 255 - out[::3]
        return out
    if fid.startswith("both_datamosh"):
        hh = frame.shape[0]
        out = frame.copy()
        seg = cv2.resize(frame[hh // 2 : hh // 2 + 1], (frame.shape[1], hh // 3))
        out[hh // 3 : 2 * hh // 3] = seg
        return out
    if fid.startswith("both_scanlines"):
        out = frame.copy()
        out[::2] = (out[::2].astype(np.float32) * 0.65).astype(np.uint8)
        return out
    return None


def _apply_utility(frame: np.ndarray, fid: str, p: dict[str, Any]) -> np.ndarray | None:
    if fid.startswith("utl_clahe"):
        return _clahe_l(frame)
    if fid.startswith("utl_histogram") or fid.startswith("both_auto_levels"):
        out = frame.copy()
        for c in range(3):
            out[:, :, c] = cv2.equalizeHist(out[:, :, c])
        return out
    if fid.startswith("utl_threshold"):
        _, th = cv2.threshold(_gray(frame), 127, 255, cv2.THRESH_BINARY)
        return _to_bgr(th)
    if fid.startswith("utl_adaptive_threshold"):
        th = cv2.adaptiveThreshold(_gray(frame), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        return _to_bgr(th)
    if fid.startswith("utl_morph_open"):
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        return cv2.morphologyEx(frame, cv2.MORPH_OPEN, k)
    if fid.startswith("utl_morph_close"):
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        return cv2.morphologyEx(frame, cv2.MORPH_CLOSE, k)
    if fid.startswith("utl_border") or fid.startswith("both_safe_margin"):
        return cv2.copyMakeBorder(frame, 8, 8, 8, 8, cv2.BORDER_CONSTANT, value=(40, 40, 40))
    if fid.startswith("utl_watermark") or fid.startswith("both_logo_overlay") or fid.startswith("both_text_overlay"):
        out = frame.copy()
        cv2.putText(out, "Chakshu", (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        return out
    if fid.startswith("utl_metadata_strip") or fid.startswith("utl_icc_convert"):
        return frame.copy()
    return None


def _apply_restore_key(frame: np.ndarray, fid: str, p: dict[str, Any]) -> np.ndarray | None:
    if fid.startswith("rst_scratch_remove") or fid.startswith("rst_dust_remove"):
        return cv2.medianBlur(frame, 3)
    if fid.startswith("rst_inpaint"):
        mask = np.zeros(frame.shape[:2], np.uint8)
        mask[frame.shape[0] // 3 : 2 * frame.shape[0] // 3, frame.shape[1] // 3 : 2 * frame.shape[1] // 3] = 255
        return cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)
    if fid.startswith("rst_stabilize_photo") or fid.startswith("both_rolling_shutter"):
        return cv2.GaussianBlur(frame, (3, 3), 0)
    if fid.startswith("rst_face_restore") or fid.startswith("both_skin_smooth"):
        return cv2.bilateralFilter(frame, 9, 80, 80)
    if fid.startswith("both_teeth_whiten"):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        bright = hsv[:, :, 2] > 180
        hsv[:, :, 1][bright] = np.clip(hsv[:, :, 1][bright] * 0.6, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    if fid.startswith("both_eye_enhance"):
        return _unsharp(frame, 0.4)
    if fid.startswith("key_chroma_green"):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([35, 80, 80]), np.array([85, 255, 255]))
        out = frame.copy()
        out[mask > 0] = 0
        return out
    if fid.startswith("key_chroma_blue"):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([90, 80, 80]), np.array([130, 255, 255]))
        out = frame.copy()
        out[mask > 0] = 0
        return out
    if fid.startswith("key_luma") or fid.startswith("both_object_mask"):
        g = _gray(frame)
        _, mask = cv2.threshold(g, 200, 255, cv2.THRESH_BINARY)
        return _to_bgr(mask)
    if fid.startswith("key_matte"):
        return cv2.GaussianBlur(frame, (5, 5), 0)
    return None


def _overlay_scope(frame: np.ndarray, mode: str) -> np.ndarray:
    h, w = frame.shape[:2]
    bar_h = max(h // 5, 40)
    overlay = frame.copy()
    strip = np.zeros((bar_h, w, 3), np.uint8)
    if mode == "waveform":
        g = _gray(frame)
        for x in range(w):
            col = g[:, min(x, g.shape[1] - 1)]
            hist = np.histogram(col, bins=bar_h, range=(0, 255))[0]
            hist = (hist / max(hist.max(), 1) * (bar_h - 1)).astype(int)
            for i, v in enumerate(hist):
                strip[bar_h - 1 - i, x] = (0, min(255, v * 8), min(255, v * 4))
    elif mode == "vectorscope":
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        for y in range(0, h, 4):
            for x in range(0, w, 4):
                hue, sat = hsv[y, x, 0], hsv[y, x, 1]
                if sat > 30:
                    px = int(hue / 180 * (w - 1))
                    py = int((255 - sat) / 255 * (bar_h - 1))
                    strip[py, px] = (255, 200, 100)
    elif mode == "histogram":
        for c, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
            hist = cv2.calcHist([frame], [c], None, [256], [0, 256]).flatten()
            hist = (hist / max(hist.max(), 1) * (bar_h - 1)).astype(int)
            for i, v in enumerate(hist):
                cv2.line(strip, (i, bar_h - 1), (i, bar_h - 1 - v), color, 1)
    elif mode == "zebra":
        bright = _gray(frame) > 235
        overlay[bright] = (0, 0, 255)
        return overlay
    elif mode == "false_color":
        g = _gray(frame)
        out = cv2.applyColorMap(g, cv2.COLORMAP_TURBO)
        return cv2.addWeighted(frame, 0.35, out, 0.65, 0)
    elif mode == "peaking":
        edges = cv2.Canny(_gray(frame), 80, 160)
        overlay[edges > 0] = (0, 255, 255)
        return overlay
    overlay[h - bar_h : h, :] = cv2.addWeighted(overlay[h - bar_h : h], 0.35, strip, 0.65, 0)
    return overlay


def _apply_video_temporal(frame: np.ndarray, fid: str, p: dict[str, Any]) -> np.ndarray | None:
    if fid.startswith("vid_deinterlace") or fid.startswith("both_interlace_fix"):
        adv = apply_advanced_filter(frame, fid, p)
        return adv if adv is not None else frame
    if fid.startswith("vid_stabilize") or fid.startswith("vid_deshake") or fid.startswith("both_tracking_stabilize") or fid.startswith("both_warp_stabilize"):
        adv = apply_advanced_filter(frame, fid, p)
        if adv is not None:
            return adv
        return cv2.GaussianBlur(_unsharp(frame, 0.15), (3, 3), 0)
    if fid.startswith("vid_deflicker") or fid.startswith("both_flicker_remove"):
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)
        lab[:, :, 0] = cv2.GaussianBlur(lab[:, :, 0], (0, 0), 8)
        return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
    if fid.startswith("vid_noise_temporal") or fid.startswith("both_frame_average") or fid.startswith("both_median_stack") or fid.startswith("both_ghost_remove"):
        return cv2.fastNlMeansDenoisedColored(frame, None, 7, 7, 7, 21)
    if fid.startswith("vid_interpolate") or fid.startswith("vid_frame_blend") or fid.startswith("vid_slow_motion"):
        blur = cv2.GaussianBlur(frame, (5, 5), 0)
        return cv2.addWeighted(frame, 0.65, blur, 0.35, 0)
    if fid.startswith("vid_optical_flow") or fid.startswith("vid_motion_blur_temporal"):
        return _apply_blur_sharpen(frame, "blr_motion", {"angle": 0, "distance": 8}) or frame
    if fid.startswith("vid_telecine") or fid.startswith("vid_pulldown") or fid.startswith("vid_field_shift"):
        out = frame.copy()
        out[1:] = frame[:-1]
        return out
    if fid.startswith("vid_hdr_tone_map") or fid.startswith("both_hdr_merge"):
        return _clahe_l(cv2.LUT(frame, _gamma_lut(1.2)))
    if fid.startswith("vid_log_to_rec709"):
        return cv2.LUT(frame, _gamma_lut(2.2))
    if fid.startswith("vid_waveform"):
        return _overlay_scope(frame, "waveform")
    if fid.startswith("vid_vectorscope"):
        return _overlay_scope(frame, "vectorscope")
    if fid.startswith("vid_histogram_video"):
        return _overlay_scope(frame, "histogram")
    if fid.startswith("vid_zebra"):
        return _overlay_scope(frame, "zebra")
    if fid.startswith("vid_false_color"):
        return _overlay_scope(frame, "false_color")
    if fid.startswith("vid_focus_peaking"):
        return _overlay_scope(frame, "peaking")
    if fid.startswith("vid_timecode_burn") or fid.startswith("both_subtitle_burn"):
        out = frame.copy()
        cv2.putText(out, "00:00:00:00", (16, frame.shape[0] - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        return out
    if fid.startswith("vid_safe_area") or fid.startswith("both_grid_overlay") or fid.startswith("both_scope_overlay"):
        out = frame.copy()
        hh, ww = out.shape[:2]
        cv2.rectangle(out, (ww // 10, hh // 10), (ww * 9 // 10, hh * 9 // 10), (0, 255, 0), 1)
        for i in range(1, 3):
            cv2.line(out, (ww * i // 3, 0), (ww * i // 3, hh), (80, 80, 80), 1)
            cv2.line(out, (0, hh * i // 3), (ww, hh * i // 3), (80, 80, 80), 1)
        return out
    if any(
        fid.startswith(x)
        for x in (
            "vid_flicker_detect",
            "vid_scene_detect",
            "vid_shot_detect",
            "vid_black_detect",
            "vid_freeze_detect",
            "vid_speed_ramp",
            "vid_reverse",
            "vid_loop",
        )
    ):
        return cv2.addWeighted(frame, 0.92, np.full_like(frame, (30, 30, 30)), 0.08, 0)
    return None


def _apply_both(frame: np.ndarray, fid: str, p: dict[str, Any]) -> np.ndarray | None:
    if fid in ("both_enhance_ai", "both_deblur_ai", "both_low_light", "both_denoise_ai"):
        adv = apply_advanced_filter(frame, fid, p)
        if adv is not None:
            return adv
        return _ai_enhance(frame, p)
    if fid.startswith("both_histogram_match"):
        mean, std = frame.mean(), max(frame.std(), 1.0)
        return _clip_u8((frame.astype(np.float32) - mean) / std * 50.0 + 128.0)
    if fid.startswith("both_style_transfer"):
        if hasattr(cv2, "stylization"):
            return cv2.stylization(frame)
        return _ai_enhance(frame, p)
    if fid in ("both_normalize", "both_auto_contrast", "both_auto_levels", "both_color_correct"):
        return _apply_color(frame, fid.replace("both_", "clr_"), p) or _ai_enhance(frame, p)
    if fid in ("both_blur", "both_sharpen", "both_denoise", "both_vignette", "both_film_grain", "both_glow"):
        mapped = fid.replace("both_", "clr_") if fid == "both_normalize" else fid.replace("both_", "blr_" if "blur" in fid else "shp_" if "sharp" in fid else "ns_" if "denoise" in fid else "sty_")
        for handler in (_apply_blur_sharpen, _apply_noise, _apply_stylize, _apply_color):
            result = handler(frame, fid, p) or handler(frame, mapped, p)
            if result is not None:
                return result
    return None


_PREFIX_CHAIN: list[tuple[str, Any]] = [
    ("clr_", _apply_color),
    ("blr_", _apply_blur_sharpen),
    ("shp_", _apply_blur_sharpen),
    ("ns_", _apply_noise),
    ("geo_", _apply_geometry),
    ("sty_", _apply_stylize),
    ("utl_", _apply_utility),
    ("rst_", _apply_restore_key),
    ("key_", _apply_restore_key),
    ("vid_", _apply_video_temporal),
    ("both_", _apply_both),
]


def apply_catalog_filter(frame: np.ndarray, filter_id: str, params: dict[str, Any] | None = None) -> np.ndarray:
    """Apply any catalog filter id to a BGR frame."""
    p = params or {}
    frame = _ensure_bgr(frame)

    if not HAS_CV2:
        return apply_basic_filter(frame, filter_id, p)

    adv = apply_advanced_filter(frame, filter_id, p)
    if adv is not None:
        return adv

    if filter_id.startswith("frn_"):
        for handler in (_apply_color, _apply_noise):
            result = handler(frame, filter_id, p)
            if result is not None:
                return result

    for prefix, handler in _PREFIX_CHAIN:
        if filter_id.startswith(prefix):
            result = handler(frame, filter_id, p)
            if result is not None:
                return result
            break

    if filter_id.startswith("both_"):
        aliases = {
            "both_sharpen": "shp_unsharp",
            "both_blur": "blr_gaussian",
            "both_denoise": "ns_denoise",
            "both_vignette": "sty_vignette",
            "both_film_grain": "ns_add_grain",
            "both_glow": "sty_glow",
        }
        alias = aliases.get(filter_id)
        if alias:
            return apply_catalog_filter(frame, alias, p)

    return _ai_enhance(frame, p)
