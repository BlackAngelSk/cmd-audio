"""Favorites / presets library (Phase 3.5)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)

PRESETS_DIR = os.path.expanduser("~/.config/cmd-audio/presets")


@dataclass
class FavoritePreset:
    """A saved user favorite preset."""
    name: str
    theme: str = "matrix"
    sensitivity: float = 1.0
    fps: int = 30
    speed_min: float = 0.25
    speed_max: float = 3.0
    ui_style: str = "full"
    banner_text: str = ""
    params: Dict[str, Any] = field(default_factory=dict)


def ensure_presets_dir() -> None:
    os.makedirs(PRESETS_DIR, exist_ok=True)


def save_favorite(preset: FavoritePreset) -> None:
    ensure_presets_dir()
    path = os.path.join(PRESETS_DIR, f"{preset.name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(preset), f, indent=2)
    logger.info("Saved preset: %s", path)


def load_favorite(name: str) -> FavoritePreset:
    path = os.path.join(PRESETS_DIR, f"{name}.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return FavoritePreset(**data)


def list_favorites() -> List[str]:
    ensure_presets_dir()
    try:
        return [f[:-5] for f in os.listdir(PRESETS_DIR) if f.endswith(".json")]
    except FileNotFoundError:
        return []


def delete_favorite(name: str) -> bool:
    path = os.path.join(PRESETS_DIR, f"{name}.json")
    if os.path.exists(path):
        os.unlink(path)
        return True
    return False