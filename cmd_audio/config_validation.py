"""Config validation using dataclass schemas (Phase 1.6)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ConfigSchema:
    """Schema for validating cmd-audio JSON configuration files."""
    
    audio_path: str = ""
    source: str = "file"
    fps: int = 30
    play: bool = True
    seed: Optional[int] = None
    sensitivity: float = 1.0
    speed_min: float = 0.25
    speed_max: float = 3.0
    terminal_switch_min: float = 4.0
    terminal_switch_max: float = 11.0
    theme: str = "matrix"
    theme_mode: str = "manual"
    bass_threshold: float = 0.15
    banner_text: str = ""
    banner_align: str = "center"
    banner_anim: str = "off"
    banner_size: str = "normal"
    show_banner: bool = False
    record_file: str = ""
    record_mode: str = "jsonl"
    mission_timeline: bool = True
    defender_ai: bool = True
    audio_fx: bool = True
    alert_tones: bool = False
    unicode_bars: bool = False
    ui_style: str = "full"
    quality_mode: str = "auto"
    scene_sync: str = "adaptive"
    plugin: str = ""
    scene_pack: str = ""
    scene_pack_file: str = ""
    
    def validate(self) -> List[str]:
        errors: List[str] = []
        if self.fps < 1 or self.fps > 120:
            errors.append(f"fps must be between 1 and 120, got {self.fps}")
        if not (0.0 <= self.sensitivity <= 5.0):
            errors.append(f"sensitivity must be between 0.0 and 5.0, got {self.sensitivity}")
        if not (0.1 <= self.speed_min <= 10.0):
            errors.append(f"speed_min must be between 0.1 and 10.0, got {self.speed_min}")
        if not (0.1 <= self.speed_max <= 10.0):
            errors.append(f"speed_max must be between 0.1 and 10.0, got {self.speed_max}")
        if not (0.0 <= self.bass_threshold <= 1.0):
            errors.append(f"bass_threshold must be between 0.0 and 1.0, got {self.bass_threshold}")
        if self.theme_mode not in ("manual", "bass"):
            errors.append(f"theme_mode must be 'manual' or 'bass', got {self.theme_mode}")
        if self.banner_align not in ("left", "center", "right"):
            errors.append(f"banner_align must be 'left', 'center', or 'right', got {self.banner_align}")
        if self.banner_anim not in ("off", "scroll", "pulse"):
            errors.append(f"banner_anim must be 'off', 'scroll', or 'pulse', got {self.banner_anim}")
        if self.banner_size not in ("normal", "large"):
            errors.append(f"banner_size must be 'normal' or 'large', got {self.banner_size}")
        return errors
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigSchema":
        schema_dict = {}
        for field_name in cls.__dataclass_fields__:
            if field_name in data:
                schema_dict[field_name] = data[field_name]
        return cls(**schema_dict)


def validate_config_file(path: str) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        return [f"Failed to parse config file: {exc}"]
    if not isinstance(data, dict):
        return ["Config file must be a JSON object"]
    schema = ConfigSchema.from_dict(data)
    return schema.validate()


def validate_config_data(data: Dict[str, Any]) -> List[str]:
    schema = ConfigSchema.from_dict(data)
    return schema.validate()