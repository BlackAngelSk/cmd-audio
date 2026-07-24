"""Music player integration (Phase 4.3)."""

from __future__ import annotations

import subprocess
import os
import re
from typing import Optional, Dict, Any
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


class PlayerDetector:
    """Detect running music players and sync visuals."""

    def __init__(self) -> None:
        self.active_player: Optional[str] = None
        self.player_info: Dict[str, Any] = {}

    def detect(self) -> Optional[str]:
        """Detect a running music player."""
        players = {
            "mpv": ["mpv", "--list-properties"],
            "vlc": ["vlc", "--version"],
            "spotify": ["spotify", "--version"],
            "cmus": ["cmus", "--version"],
            "moc": ["mocp", "--info"],
            "pianobar": ["pianobar", "--version"],
        }
        for name, cmd in players.items():
            try:
                subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=2,
                    check=True,
                )
                self.active_player = name
                return name
            except (subprocess.CalledProcessError, FileNotFoundError, TimeoutError):
                continue
        self.active_player = None
        return None

    def get_position(self, player: Optional[str] = None) -> Dict[str, Any]:
        """Get current playback position."""
        player = player or self.active_player
        if player == "mpv":
            return self._get_mpv_position()
        elif player == "cmus":
            return self._get_cmus_position()
        elif player == "moc":
            return self._get_moc_position()
        return {"time": 0.0, "duration": 0.0}

    def _get_mpv_position(self) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["mpv", "--command", "get_property time-pos"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            time_txt = result.stdout.strip()
            if "AV_ERROR" in time_txt:
                return {"time": 0.0, "duration": 0.0}
            return {"time": float(time_txt) if time_txt else 0.0, "duration": 0.0}
        except Exception:
            return {"time": 0.0, "duration": 0.0}

    def _get_cmus_position(self) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["cmus-remote", "-C", "status"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            # Parse cmus status
            time_match = re.search(r"position (\d+)", result.stdout)
            if time_match:
                return {"time": float(time_match.group(1)), "duration": 0.0}
            return {"time": 0.0, "duration": 0.0}
        except Exception:
            return {"time": 0.0, "duration": 0.0}

    def _get_moc_position(self) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["mocp", "--info"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            time_match = re.search(r"Time: (\d+)", result.stdout)
            if time_match:
                return {"time": float(time_match.group(1)), "duration": 0.0}
            return {"time": 0.0, "duration": 0.0}
        except Exception:
            return {"time": 0.0, "duration": 0.0}


def get_active_player() -> Optional[str]:
    """Get the name of the currently active music player."""
    detector = PlayerDetector()
    return detector.detect()