"""Adaptive frame rate scaling (Phase 2.7)."""

from __future__ import annotations

import time
from typing import List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


class AdaptiveFpsController:
    """Dynamically adjusts FPS based on audio complexity and system load."""

    def __init__(self, min_fps: int = 15, max_fps: int = 120, target_fps: int = 30):
        self.min_fps = min_fps
        self.max_fps = max_fps
        self.target_fps = target_fps
        self.current_fps = target_fps
        self.history: List[float] = []
        self.max_history = 120

    def adjust(self, frame_time: float, audio_level: float, beat: bool) -> int:
        """Adjust FPS based on current conditions."""
        self.history.append(frame_time)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        avg = sum(self.history) / len(self.history) if self.history else frame_time
        if avg > 0 and audio_level > 0.5:
            target = int(1.0 / avg)
            target = max(self.min_fps, min(self.max_fps, target))
            if beat and target < self.max_fps:
                target = min(self.max_fps, target + 10)
            self.current_fps = target
        return self.current_fps

    def get_fps(self) -> int:
        return self.current_fps

    def reset(self) -> None:
        self.current_fps = self.target_fps
        self.history.clear()