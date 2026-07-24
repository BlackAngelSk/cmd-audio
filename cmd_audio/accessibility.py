"""Accessibility modes (Phase 5.6)."""

from __future__ import annotations

from typing import List
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


def high_contrast_theme(name: str = "highcontrast") -> dict:
    """Return a high-contrast theme dictionary."""
    return {
        "name": name,
        "mode": "high-contrast",
        "colors": {"text": "#FFFFFF", "bg": "#000000", "accent": "#FFD700"},
    }


def generate_screen_reader_text(lines: List[str], mode: str = "summary") -> str:
    """Generate screen-reader-friendly description of visual content."""
    if not lines:
        return "No visual content."
    if mode == "full":
        return "Visual: " + "; ".join(lines)
    # summary
    has_symbols = any(c in "".join(lines) for c in "#*@")
    if has_symbols:
        summary_lines = lines[:3]
        return "Visual: " + "; ".join(summary_lines) + "..."
    return "Visual: " + "; ".join(lines[:3])


def get_high_contrast_colors() -> dict:
    return high_contrast_theme()