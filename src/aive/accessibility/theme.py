"""Accessibility — high contrast and color-blind safe palettes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ColorBlindMode(str, Enum):
    NONE = "none"
    PROTANOPIA = "protanopia"
    DEUTERANOPIA = "deuteranopia"
    TRITANOPIA = "tritanopia"


@dataclass
class ThemeColors:
    background: str
    foreground: str
    accent: str
    panel: str
    border: str
    warning: str
    success: str


DEFAULT_THEME = ThemeColors(
    background="#1e1e2e",
    foreground="#cdd6f4",
    accent="#89b4fa",
    panel="#313244",
    border="#45475a",
    warning="#fab387",
    success="#a6e3a1",
)

HIGH_CONTRAST_THEME = ThemeColors(
    background="#000000",
    foreground="#ffffff",
    accent="#ffff00",
    panel="#1a1a1a",
    border="#ffffff",
    warning="#ff9900",
    success="#00ff00",
)

COLOR_BLIND_THEMES: dict[ColorBlindMode, ThemeColors] = {
    ColorBlindMode.PROTANOPIA: ThemeColors(
        "#1a1a2e", "#e0e0ff", "#6eb5ff", "#2d2d44", "#4a4a6a", "#ffb347", "#90ee90"
    ),
    ColorBlindMode.DEUTERANOPIA: ThemeColors(
        "#1a1a2e", "#ffe0e0", "#ff6e6e", "#2d2d44", "#6a4a4a", "#87cefa", "#dda0dd"
    ),
    ColorBlindMode.TRITANOPIA: ThemeColors(
        "#1a2e1a", "#e0ffe0", "#6eff6e", "#2d442d", "#4a6a4a", "#ff69b4", "#f0e68c"
    ),
}


def get_theme(high_contrast: bool = False, color_blind: ColorBlindMode = ColorBlindMode.NONE) -> ThemeColors:
    if high_contrast:
        return HIGH_CONTRAST_THEME
    if color_blind != ColorBlindMode.NONE:
        return COLOR_BLIND_THEMES.get(color_blind, DEFAULT_THEME)
    return DEFAULT_THEME


def stylesheet(theme: ThemeColors) -> str:
    return f"""
    QMainWindow, QWidget {{
        background-color: {theme.background};
        color: {theme.foreground};
    }}
    QMenuBar, QMenu {{
        background-color: {theme.panel};
        color: {theme.foreground};
    }}
    QPushButton {{
        background-color: {theme.accent};
        color: {theme.background};
        border: 2px solid {theme.border};
        padding: 6px 12px;
        font-weight: bold;
    }}
    QListWidget, QTreeWidget, QTextEdit {{
        background-color: {theme.panel};
        color: {theme.foreground};
        border: 1px solid {theme.border};
    }}
    QStatusBar {{
        background-color: {theme.panel};
        color: {theme.foreground};
    }}
    """
