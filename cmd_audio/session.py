"""State persistence for runtime settings (Phase 3.4)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)

SESSION_DIR = os.path.expanduser("~/.config/cmd-audio")
SESSION_FILE = os.path.join(SESSION_DIR, "state.json")


@dataclass
class SessionState:
    """Saved/loaded runtime settings."""
    theme: str = "matrix"
    sensitivity: float = 1.0
    speed_min: float = 0.25
    speed_max: float = 3.0
    fps: int = 30
    banner_text: str = ""
    banner_align: str = "center"
    banner_anim: str = "off"
    banner_size: str = "normal"
    show_banner: bool = False
    ui_style: str = "full"
    quality_mode: str = "auto"
    scene_sync: str = "adaptive"
    unicode_bars: bool = False
    alert_tones: bool = False
    mission_timeline: bool = True
    defender_ai: bool = True
    audio_fx: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        known = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


def save_session(state: SessionState) -> None:
    """Save session state to disk."""
    os.makedirs(SESSION_DIR, exist_ok=True)
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2)
        logger.info("Session saved to %s", SESSION_FILE)
    except OSError as exc:
        logger.error("Failed to save session: %s", exc)


def load_session() -> Optional[SessionState]:
    """Load session state from disk. Returns None if not found."""
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return SessionState.from_dict(data)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load session: %s", exc)
        return None


def delete_session() -> None:
    """Delete the session file."""
    if os.path.exists(SESSION_FILE):
        try:
            os.unlink(SESSION_FILE)
        except OSError:
            pass