"""Frame drop monitoring (Phase 1.10)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class FrameDropMonitor:
    """Monitors frame drop statistics."""
    expected_fps: int = 30
    max_history: int = 300
    frame_times: List[float] = field(default_factory=list)
    drop_count: int = 0
    total_frames: int = 0

    def record_frame(self, elapsed: float) -> None:
        """Record a frame's render time."""
        self.frame_times.append(elapsed)
        if len(self.frame_times) > self.max_history:
            self.frame_times.pop(0)
        self.total_frames += 1

    def mark_drop(self) -> None:
        self.drop_count += 1

    def get_drop_rate(self) -> float:
        if self.total_frames == 0:
            return 0.0
        return self.drop_count / self.total_frames

    def get_avg_fps(self) -> float:
        if not self.frame_times:
            return 0.0
        total = sum(self.frame_times)
        return len(self.frame_times) / total if total > 0 else 0.0

    def get_avg_frame_time(self) -> float:
        if not self.frame_times:
            return 0.0
        return sum(self.frame_times) / len(self.frame_times)

    def summary(self) -> str:
        return (
            f"avg_fps: {self.get_avg_fps():.1f} | "
            f"drops: {self.drop_count} ({self.get_drop_rate():.1%}) | "
            f"avg_frame: {self.get_avg_frame_time()*1000:.1f}ms"
        )

    def reset(self) -> None:
        self.frame_times.clear()
        self.drop_count = 0
        self.total_frames = 0


def create_frame_drop_monitor(expected_fps: int = 30) -> FrameDropMonitor:
    """Create a frame drop monitor."""
    return FrameDropMonitor(expected_fps=expected_fps)