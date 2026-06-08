"""i18n and accessibility preferences API (R-100, R-101)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from aive.accessibility.theme import ColorBlindMode, get_theme
from aive.i18n.forensic_strings import strings_for_locale
from aive.i18n.translations import LOCALES, get_locale_catalog

router = APIRouter(prefix="/api", tags=["i18n"])


@router.get("/i18n/locales")
def list_locales() -> dict[str, Any]:
    return {"locales": get_locale_catalog(), "default": "en"}


@router.get("/i18n/{locale}")
def get_locale_strings(locale: str) -> dict[str, Any]:
    if locale not in LOCALES:
        raise HTTPException(404, f"Unknown locale: {locale}")
    return {"locale": locale, "strings": strings_for_locale(locale)}


@router.get("/accessibility/options")
def accessibility_options() -> dict[str, Any]:
    return {
        "color_blind_modes": [
            {"id": "none", "label_key": "settings.color_blind.none"},
            {"id": "protanopia", "label_key": "settings.color_blind.protanopia"},
            {"id": "deuteranopia", "label_key": "settings.color_blind.deuteranopia"},
            {"id": "tritanopia", "label_key": "settings.color_blind.tritanopia"},
        ],
        "font_scales": [100, 110, 125, 150],
        "features": ["high_contrast", "color_blind", "font_scale", "reduce_motion", "focus_visible"],
    }


@router.get("/accessibility/theme")
def accessibility_theme(
    high_contrast: bool = False,
    color_blind: str = "none",
) -> dict[str, Any]:
    try:
        mode = ColorBlindMode(color_blind)
    except ValueError:
        mode = ColorBlindMode.NONE
    theme = get_theme(high_contrast, mode)
    return {
        "background": theme.background,
        "foreground": theme.foreground,
        "accent": theme.accent,
        "panel": theme.panel,
        "border": theme.border,
        "warning": theme.warning,
        "success": theme.success,
    }
