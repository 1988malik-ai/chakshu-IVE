"""Filter catalog: 140+ image and video processing filters."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class FilterDomain(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    BOTH = "both"


class FilterCategory(str, Enum):
    COLOR = "color"
    TONE = "tone"
    SHARPEN = "sharpen"
    BLUR = "blur"
    NOISE = "noise"
    GEOMETRIC = "geometric"
    STYLIZE = "stylize"
    RESTORE = "restore"
    ILLUMINATION = "illumination"
    TEMPORAL = "temporal"
    MOTION = "motion"
    KEYING = "keying"
    UTILITY = "utility"
    AI = "ai"


@dataclass(frozen=True)
class FilterSpec:
    id: str
    name: str
    category: FilterCategory
    domain: FilterDomain
    description: str = ""
    params: dict[str, Any] = field(default_factory=dict)


def _img(
    fid: str,
    name: str,
    cat: FilterCategory,
    desc: str = "",
    **params: Any,
) -> FilterSpec:
    return FilterSpec(fid, name, cat, FilterDomain.IMAGE, desc, dict(params))


def _vid(
    fid: str,
    name: str,
    cat: FilterCategory,
    desc: str = "",
    **params: Any,
) -> FilterSpec:
    return FilterSpec(fid, name, cat, FilterDomain.VIDEO, desc, dict(params))


def _both(
    fid: str,
    name: str,
    cat: FilterCategory,
    desc: str = "",
    **params: Any,
) -> FilterSpec:
    return FilterSpec(fid, name, cat, FilterDomain.BOTH, desc, dict(params))


# --- 140+ filters ---
FILTER_CATALOG: list[FilterSpec] = [
    # Color & tone (image)
    _img("clr_brightness", "Brightness", FilterCategory.COLOR, amount=0.0),
    _img("clr_contrast", "Contrast", FilterCategory.COLOR, amount=1.0),
    _img("clr_saturation", "Saturation", FilterCategory.COLOR, amount=1.0),
    _img("clr_hue", "Hue Shift", FilterCategory.COLOR, degrees=0.0),
    _img("clr_vibrance", "Vibrance", FilterCategory.COLOR, amount=0.0),
    _img("clr_exposure", "Exposure", FilterCategory.TONE, stops=0.0),
    _img("clr_gamma", "Gamma", FilterCategory.TONE, gamma=1.0),
    _img("clr_levels", "Levels", FilterCategory.TONE),
    _img("clr_curves", "Curves", FilterCategory.TONE),
    _img("clr_white_balance", "White Balance", FilterCategory.COLOR),
    _img("clr_temperature", "Color Temperature", FilterCategory.COLOR, kelvin=6500),
    _img("clr_tint", "Tint", FilterCategory.COLOR, amount=0.0),
    _img("clr_shadows", "Shadows", FilterCategory.TONE),
    _img("clr_highlights", "Highlights", FilterCategory.TONE),
    _img("clr_midtones", "Midtones", FilterCategory.TONE),
    _img("clr_black_point", "Black Point", FilterCategory.TONE),
    _img("clr_white_point", "White Point", FilterCategory.TONE),
    _img("clr_clarity", "Clarity", FilterCategory.TONE, amount=0.0),
    _img("clr_dehaze", "Dehaze", FilterCategory.RESTORE, strength=0.5),
    _img("clr_fade", "Fade", FilterCategory.STYLIZE, amount=0.0),
    _img("clr_sepia", "Sepia", FilterCategory.STYLIZE, amount=0.0),
    _img("clr_grayscale", "Grayscale", FilterCategory.STYLIZE),
    _img("clr_invert", "Invert", FilterCategory.STYLIZE),
    _img("clr_posterize", "Posterize", FilterCategory.STYLIZE, levels=8),
    _img("clr_solarize", "Solarize", FilterCategory.STYLIZE),
    _img("clr_channel_mixer", "Channel Mixer", FilterCategory.COLOR),
    _img("clr_color_balance", "Color Balance", FilterCategory.COLOR),
    _img("clr_selective_color", "Selective Color", FilterCategory.COLOR),
    _img("clr_lut_cube", "3D LUT (CUBE)", FilterCategory.COLOR),
    _img("clr_lut_hald", "HALD LUT", FilterCategory.COLOR),
    _img("clr_film_emulation", "Film Emulation", FilterCategory.STYLIZE),
    # Sharpen & blur (image)
    _img("shp_unsharp", "Unsharp Mask", FilterCategory.SHARPEN, radius=1.0, amount=1.0),
    _img("shp_high_pass", "High Pass Sharpen", FilterCategory.SHARPEN),
    _img("shp_smart_sharpen", "Smart Sharpen", FilterCategory.SHARPEN),
    _img("shp_edge_enhance", "Edge Enhance", FilterCategory.SHARPEN),
    _img("shp_detail", "Detail Enhancement", FilterCategory.SHARPEN),
    _img("blr_gaussian", "Gaussian Blur", FilterCategory.BLUR, radius=3.0),
    _img("blr_box", "Box Blur", FilterCategory.BLUR, radius=3.0),
    _img("blr_motion", "Motion Blur", FilterCategory.BLUR, angle=0, distance=10),
    _img("blr_radial", "Radial Blur", FilterCategory.BLUR),
    _img("blr_zoom", "Zoom Blur", FilterCategory.BLUR),
    _img("blr_lens", "Lens Blur", FilterCategory.BLUR, radius=5.0),
    _img("blr_surface", "Surface Blur", FilterCategory.BLUR),
    _img("blr_median", "Median Blur", FilterCategory.BLUR, ksize=5),
    _img("blr_bilateral", "Bilateral Filter", FilterCategory.BLUR),
    _img("blr_stack", "Stack Blur", FilterCategory.BLUR),
    # Noise (image)
    _img("ns_denoise", "Denoise", FilterCategory.NOISE, strength=0.5),
    _img("ns_nlmeans", "NL-Means Denoise", FilterCategory.NOISE),
    _img("ns_median_denoise", "Median Denoise", FilterCategory.NOISE),
    _img("ns_gaussian_denoise", "Gaussian Denoise", FilterCategory.NOISE),
    _img("ns_add_grain", "Film Grain", FilterCategory.NOISE, amount=0.2),
    _img("ns_add_noise", "Add Noise", FilterCategory.NOISE),
    _img("ns_remove_hot_pixels", "Hot Pixel Removal", FilterCategory.NOISE),
    _img("ns_impulse", "Impulse Noise Removal", FilterCategory.NOISE),
    # Geometric (image)
    _img("geo_crop", "Crop", FilterCategory.GEOMETRIC),
    _img("geo_resize", "Resize", FilterCategory.GEOMETRIC),
    _img("geo_rotate", "Rotate", FilterCategory.GEOMETRIC, angle=0),
    _img("geo_flip_h", "Flip Horizontal", FilterCategory.GEOMETRIC),
    _img("geo_flip_v", "Flip Vertical", FilterCategory.GEOMETRIC),
    _img("geo_perspective", "Perspective", FilterCategory.GEOMETRIC),
    _img("geo_lens_distort", "Lens Distortion", FilterCategory.GEOMETRIC),
    _img("geo_barrel", "Barrel Distortion", FilterCategory.GEOMETRIC),
    _img("geo_pincushion", "Pincushion", FilterCategory.GEOMETRIC),
    _img("geo_keystone", "Keystone Correction", FilterCategory.GEOMETRIC),
    _img("geo_warp", "Mesh Warp", FilterCategory.GEOMETRIC),
    _img("geo_liquify", "Liquify", FilterCategory.GEOMETRIC),
    # Stylize (image)
    _img("sty_emboss", "Emboss", FilterCategory.STYLIZE),
    _img("sty_edge_detect", "Edge Detect", FilterCategory.STYLIZE),
    _img("sty_canny", "Canny Edges", FilterCategory.STYLIZE),
    _img("sty_oil_paint", "Oil Paint", FilterCategory.STYLIZE),
    _img("sty_cartoon", "Cartoon", FilterCategory.STYLIZE),
    _img("sty_pixelate", "Pixelate", FilterCategory.STYLIZE, block=8),
    _img("sty_mosaic", "Mosaic", FilterCategory.STYLIZE),
    _img("sty_halftone", "Halftone", FilterCategory.STYLIZE),
    _img("sty_vignette", "Vignette", FilterCategory.STYLIZE, amount=0.5),
    _img("sty_glow", "Glow", FilterCategory.STYLIZE),
    _img("sty_bloom", "Bloom", FilterCategory.STYLIZE),
    _img("sty_chromatic_aberration", "Chromatic Aberration", FilterCategory.STYLIZE),
    # Restore (image)
    _img("rst_sharpen_ai", "AI Sharpen", FilterCategory.AI),
    _img("rst_upscale", "Upscale", FilterCategory.RESTORE, scale=2),
    _img("rst_super_resolution", "Super Resolution", FilterCategory.AI),
    _img("rst_face_restore", "Face Restore", FilterCategory.AI),
    _img("rst_scratch_remove", "Scratch Removal", FilterCategory.RESTORE),
    _img("rst_dust_remove", "Dust Removal", FilterCategory.RESTORE),
    _img("rst_inpaint", "Content-Aware Fill", FilterCategory.RESTORE),
    _img("rst_defog", "Defog", FilterCategory.RESTORE),
    _img("rst_stabilize_photo", "Photo Stabilize", FilterCategory.RESTORE),
    _img("rst_jpeg_artifact", "JPEG Artifact Reduction", FilterCategory.RESTORE, strength=0.6),
    # Illumination adjustment (forensic lighting normalization)
    _both(
        "ill_homomorphic",
        "Homomorphic Filter",
        FilterCategory.ILLUMINATION,
        "Suppress uneven illumination via log-frequency filtering (R-153)",
        sigma=30.0,
        order=0.5,
    ),
    _both(
        "ill_retinex",
        "Multi-Scale Retinex",
        FilterCategory.ILLUMINATION,
        "Retinex illumination normalization for shadow/highlight balance",
        scales="15,80,250",
        gain=1.0,
    ),
    _both(
        "ill_adaptive_flatten",
        "Adaptive Illumination Flatten",
        FilterCategory.ILLUMINATION,
        "Divide luminance by Gaussian envelope to flatten uneven lighting",
        sigma=40.0,
    ),
    _both(
        "ill_clahe_luminance",
        "CLAHE Luminance",
        FilterCategory.ILLUMINATION,
        "Local contrast enhancement on luminance channel",
        clip=2.0,
    ),
    _both(
        "ill_shadow_lift",
        "Shadow Lift",
        FilterCategory.ILLUMINATION,
        "Lift dark regions while preserving highlights",
        amount=0.35,
    ),
    # Advanced (Section 16)
    _img(
        "adv_homomorphic",
        "Homomorphic Filter (advanced)",
        FilterCategory.ILLUMINATION,
        "Alias for homomorphic illumination filter — use ill_homomorphic for video frames",
        sigma=30.0,
        order=0.5,
    ),
    _img("adv_auto_contrast", "Auto Contrast + Halo Suppress", FilterCategory.TONE, clip=2.5),
    _img("adv_color_separate", "Color Channel Isolate", FilterCategory.COLOR, channel="r"),
    _img("adv_motion_deblur", "Motion Deblur", FilterCategory.RESTORE, strength=0.6),
    _img("adv_jpeg_artifact", "JPEG De-artifact", FilterCategory.RESTORE, strength=0.6),
    _img("adv_channel_replace", "Channel Invert/Replace", FilterCategory.COLOR, channel="g", mode="invert"),
    _img("adv_super_resolution", "Super Resolution", FilterCategory.AI, scale=2.0),
    _img("adv_panorama", "Panoramic Unwrap (wide)", FilterCategory.GEOMETRIC, fov=100.0),
    _img(
        "adv_omni_panorama",
        "Omnidirectional → Panorama",
        FilterCategory.GEOMETRIC,
        "Convert fisheye / 360° sources to equirectangular, cylindrical, or rectilinear views",
        source_type="fisheye",
        output_type="equirectangular",
        fov_deg=180.0,
        fisheye_model="equidistant",
        yaw_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        fov_h_deg=90.0,
        fov_v_deg=60.0,
    ),
    _img("adv_deinterlace", "Deinterlace Frame", FilterCategory.TEMPORAL, mode="bob"),
    _img("adv_interlace", "Interlace Fields", FilterCategory.TEMPORAL, field="top"),
    _img("adv_perspective", "Perspective Stabilize", FilterCategory.GEOMETRIC),
    # Keying (image)
    _img("key_chroma_green", "Chroma Key Green", FilterCategory.KEYING),
    _img("key_chroma_blue", "Chroma Key Blue", FilterCategory.KEYING),
    _img("key_luma", "Luma Key", FilterCategory.KEYING),
    _img("key_matte", "Refine Matte", FilterCategory.KEYING),
    # Utility (image)
    _img("utl_histogram", "Histogram Equalize", FilterCategory.UTILITY),
    _img("utl_clahe", "CLAHE", FilterCategory.UTILITY),
    _img("utl_threshold", "Threshold", FilterCategory.UTILITY),
    _img("utl_adaptive_threshold", "Adaptive Threshold", FilterCategory.UTILITY),
    _img("utl_morph_open", "Morphology Open", FilterCategory.UTILITY),
    _img("utl_morph_close", "Morphology Close", FilterCategory.UTILITY),
    _img("utl_border", "Add Border", FilterCategory.UTILITY),
    _img("utl_watermark", "Watermark", FilterCategory.UTILITY),
    _img("utl_metadata_strip", "Strip Metadata", FilterCategory.UTILITY),
    _img("utl_icc_convert", "ICC Profile Convert", FilterCategory.UTILITY),
    # Video temporal & motion
    _vid("vid_stabilize", "Video Stabilize", FilterCategory.TEMPORAL),
    _vid("vid_deshake", "Deshake", FilterCategory.TEMPORAL),
    _vid("vid_deflicker", "Deflicker", FilterCategory.TEMPORAL),
    _vid("vid_interpolate", "Frame Interpolation", FilterCategory.TEMPORAL),
    _vid("vid_slow_motion", "Slow Motion", FilterCategory.TEMPORAL, factor=0.5),
    _vid("vid_speed_ramp", "Speed Ramp", FilterCategory.TEMPORAL),
    _vid("vid_reverse", "Reverse", FilterCategory.TEMPORAL),
    _vid("vid_loop", "Loop Segment", FilterCategory.TEMPORAL),
    _vid("vid_frame_blend", "Frame Blend", FilterCategory.TEMPORAL),
    _vid("vid_optical_flow", "Optical Flow Smooth", FilterCategory.MOTION),
    _vid("vid_motion_blur_temporal", "Temporal Motion Blur", FilterCategory.MOTION),
    _vid("vid_deinterlace", "Deinterlace", FilterCategory.TEMPORAL),
    _vid("vid_telecine", "Telecine Inverse", FilterCategory.TEMPORAL),
    _vid("vid_pulldown", "Pulldown Removal", FilterCategory.TEMPORAL),
    _vid("vid_field_shift", "Field Shift", FilterCategory.TEMPORAL),
    _vid("vid_noise_temporal", "Temporal Denoise", FilterCategory.NOISE),
    _vid("vid_flicker_detect", "Flicker Detect", FilterCategory.UTILITY),
    _vid("vid_scene_detect", "Scene Detection", FilterCategory.UTILITY),
    _vid("vid_shot_detect", "Shot Boundary", FilterCategory.UTILITY),
    _vid("vid_black_detect", "Black Frame Detect", FilterCategory.UTILITY),
    _vid("vid_freeze_detect", "Freeze Frame Detect", FilterCategory.UTILITY),
    _vid("vid_timecode_burn", "Timecode Burn-in", FilterCategory.UTILITY),
    _vid("vid_safe_area", "Safe Area Overlay", FilterCategory.UTILITY),
    _vid("vid_letterbox", "Letterbox", FilterCategory.GEOMETRIC),
    _vid("vid_pillarbox", "Pillarbox", FilterCategory.GEOMETRIC),
    _vid("vid_crop_detect", "Auto Crop Detect", FilterCategory.GEOMETRIC),
    _vid("vid_aspect_fix", "Aspect Ratio Fix", FilterCategory.GEOMETRIC),
    _vid("vid_rotate_90", "Rotate 90°", FilterCategory.GEOMETRIC),
    _vid("vid_flip", "Flip Video", FilterCategory.GEOMETRIC),
    _vid("vid_scale", "Scale Video", FilterCategory.GEOMETRIC),
    _vid("vid_pad", "Pad Video", FilterCategory.GEOMETRIC),
    _vid("vid_crop", "Crop Video", FilterCategory.GEOMETRIC),
    # Video color (shared pipeline)
    _vid("vid_color_grade", "Color Grade", FilterCategory.COLOR),
    _vid("vid_lut", "Video LUT", FilterCategory.COLOR),
    _vid("vid_hdr_tone_map", "HDR Tone Map", FilterCategory.TONE),
    _vid("vid_log_to_rec709", "Log to Rec.709", FilterCategory.TONE),
    _vid("vid_waveform", "Waveform Monitor", FilterCategory.UTILITY),
    _vid("vid_vectorscope", "Vectorscope", FilterCategory.UTILITY),
    _vid("vid_histogram_video", "Video Histogram", FilterCategory.UTILITY),
    _vid("vid_zebra", "Zebra Stripes", FilterCategory.UTILITY),
    _vid("vid_false_color", "False Color Exposure", FilterCategory.UTILITY),
    _vid("vid_focus_peaking", "Focus Peaking", FilterCategory.UTILITY),
    # Both domains
    _both("both_sharpen", "Sharpen", FilterCategory.SHARPEN),
    _both("both_blur", "Blur", FilterCategory.BLUR),
    _both("both_denoise", "Denoise", FilterCategory.NOISE),
    _both("both_color_correct", "Auto Color Correct", FilterCategory.COLOR),
    _both("both_auto_levels", "Auto Levels", FilterCategory.TONE),
    _both("both_auto_contrast", "Auto Contrast", FilterCategory.TONE),
    _both("both_normalize", "Normalize", FilterCategory.UTILITY),
    _both("both_histogram_match", "Histogram Match", FilterCategory.COLOR),
    _both("both_style_transfer", "Neural Style Transfer", FilterCategory.AI),
    _both("both_denoise_ai", "AI Denoise", FilterCategory.AI),
    _both("both_enhance_ai", "AI Enhance", FilterCategory.AI),
    _both("both_upscale_ai", "AI Upscale", FilterCategory.AI),
    _both("both_deblur_ai", "AI Deblur", FilterCategory.AI),
    _both("both_low_light", "AI Low-Light", FilterCategory.AI),
    _both("both_hdr_merge", "HDR Merge", FilterCategory.TONE),
    _both("both_perspective_match", "Perspective Match", FilterCategory.GEOMETRIC),
    _both("both_lens_correction", "Lens Correction", FilterCategory.GEOMETRIC),
    _both("both_vignette", "Vignette", FilterCategory.STYLIZE),
    _both("both_film_grain", "Film Grain", FilterCategory.STYLIZE),
    _both("both_glow", "Glow", FilterCategory.STYLIZE),
    _both("both_edge_glow", "Edge Glow", FilterCategory.STYLIZE),
    _both("both_pixel_sort", "Pixel Sort", FilterCategory.STYLIZE),
    _both("both_glitch", "Glitch", FilterCategory.STYLIZE),
    _both("both_datamosh", "Datamosh", FilterCategory.STYLIZE),
    _both("both_rgb_split", "RGB Split", FilterCategory.STYLIZE),
    _both("both_scanlines", "Scanlines", FilterCategory.STYLIZE),
    _both("both_noise_reduction_broadcast", "Broadcast NR", FilterCategory.NOISE),
    _both("both_skin_smooth", "Skin Smooth", FilterCategory.RESTORE),
    _both("both_teeth_whiten", "Teeth Whiten", FilterCategory.RESTORE),
    _both("both_eye_enhance", "Eye Enhance", FilterCategory.RESTORE),
    _both("both_background_blur", "Background Blur", FilterCategory.BLUR),
    _both("both_depth_blur", "Depth Blur", FilterCategory.BLUR),
    _both("both_object_mask", "Object Mask", FilterCategory.KEYING),
    _both("both_tracking_stabilize", "Tracking Stabilize", FilterCategory.MOTION),
    _both("both_motion_track_blur", "Motion Track Blur", FilterCategory.MOTION),
    _both("both_warp_stabilize", "Warp Stabilize", FilterCategory.MOTION),
    _both("both_rolling_shutter", "Rolling Shutter Fix", FilterCategory.RESTORE),
    _both("both_flicker_remove", "Flicker Remove", FilterCategory.TEMPORAL),
    _both("both_interlace_fix", "Interlace Fix", FilterCategory.TEMPORAL),
    _both("both_frame_average", "Frame Average", FilterCategory.TEMPORAL),
    _both("both_median_stack", "Median Stack", FilterCategory.TEMPORAL),
    _both("both_ghost_remove", "Ghost Removal", FilterCategory.TEMPORAL),
    _both("both_logo_overlay", "Logo Overlay", FilterCategory.UTILITY),
    _both("both_text_overlay", "Text Overlay", FilterCategory.UTILITY),
    _both("both_subtitle_burn", "Subtitle Burn-in", FilterCategory.UTILITY),
    _both("both_safe_margin", "Safe Margins", FilterCategory.UTILITY),
    _both("both_grid_overlay", "Grid Overlay", FilterCategory.UTILITY),
    _both("both_scope_overlay", "Scope Overlay", FilterCategory.UTILITY),
]

assert len(FILTER_CATALOG) >= 140, f"Expected 140+ filters, got {len(FILTER_CATALOG)}"


_FILTER_BY_ID: dict[str, FilterSpec] = {f.id: f for f in FILTER_CATALOG}


def get_filter(filter_id: str) -> FilterSpec | None:
    return _FILTER_BY_ID.get(filter_id)


def list_filters(
    domain: FilterDomain | None = None,
    category: FilterCategory | None = None,
) -> list[FilterSpec]:
    out = FILTER_CATALOG
    if domain:
        out = [f for f in out if f.domain in (domain, FilterDomain.BOTH)]
    if category:
        out = [f for f in out if f.category == category]
    return out


def filter_count() -> int:
    return len(FILTER_CATALOG)
