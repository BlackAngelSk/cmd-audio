"""Custom color themes from JSON files (Phase 2.4)."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)

CUSTOM_THEME_DIR = os.path.expanduser("~/.config/cmd-audio/themes")


def ensure_theme_dir() -> None:
    """Ensure the custom themes directory exists."""
    os.makedirs(CUSTOM_THEME_DIR, exist_ok=True)


def load_custom_themes() -> Dict[str, Tuple[str, str, str]]:
    """Load all custom themes from the themes directory."""
    ensure_theme_dir()
    themes: Dict[str, Tuple[str, str, str]] = {}
    if not os.path.isdir(CUSTOM_THEME_DIR):
        return themes
    for filename in os.listdir(CUSTOM_THEME_DIR):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(CUSTOM_THEME_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                continue
            name = data.get("name", filename[:-5])
            colors = data.get("colors", [])
            if isinstance(colors, list) and len(colors) == 3:
                themes[name] = tuple(colors)  # type: ignore
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load custom theme %s: %s", filepath, exc)
    return themes


def save_custom_theme(name: str, colors: Tuple[str, str, str]) -> None:
    """Save a custom theme."""
    ensure_theme_dir()
    filepath = os.path.join(CUSTOM_THEME_DIR, f"{name}.json")
    data = {"name": name, "colors": list(colors)}
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("Saved custom theme: %s", filepath)


def get_all_themes() -> Dict[str, Tuple[str, str, str]]:
    """Get all themes including custom ones."""
    from cmd_audio.config import THEMES
    all_themes = dict(THEMES)
    all_themes.update(load_custom_themes())
    return all_themes