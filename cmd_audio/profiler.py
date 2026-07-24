"""Performance profiling for cmd-audio (Phase 1.9)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ProfileStats:
    """Accumulated profiling statistics."""
    frame_times: List[float] = field(default_factory=list)
    audio_analysis_times: List[float] = field(default_factory=list)
    render_times: List[float] = field(default_factory=list)
    input_times: List[float] = field(default_factory=list)
    total_frames: int = 0
    skipped_frames: int = 0
    start_time: float = 0.0

    def avg_frame_time(self) -> float:
        if not self.frame_times:
            return 0.0
        return sum(self.frame_times) / len(self.frame_times)

    def avg_render_time(self) -> float:
        if not self.render_times:
            return 0.0
        return sum(self.render_times) / len(self.render_times)

    def avg_audio_analysis_time(self) -> float:
        if not self.audio_analysis_times:
            return 0.0
        return sum(self.audio_analysis_times) / len(self.audio_analysis_times)

    def fps_achieved(self) -> float:
        elapsed = time.perf_counter() - self.start_time
        if elapsed <= 0:
            return 0.0
        return self.total_frames / elapsed

    def summary(self) -> Dict[str, float]:
        return {
            "avg_frame_ms": self.avg_frame_time() * 1000,
            "avg_render_ms": self.avg_render_time() * 1000,
            "avg_audio_ms": self.avg_audio_analysis_time() * 1000,
            "fps_achieved": self.fps_achieved(),
            "total_frames": float(self.total_frames),
            "skipped_frames": float(self.skipped_frames),
        }


class Profiler:
    """Context-manager-based profiler for frame rendering."""

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled
        self.stats = ProfileStats(start_time=time.perf_counter())

    def start_frame(self) -> None:
        self._frame_start = time.perf_counter()

    def end_frame(self) -> None:
        elapsed = time.perf_counter() - self._frame_start
        self.stats.frame_times.append(elapsed)
        self.stats.total_frames += 1

    def track_render(self, func) -> None:
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        self.stats.render_times.append(elapsed)
        return result

    def track_audio(self, func) -> None:
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        self.stats.audio_analysis_times.append(elapsed)
        return result

    def report(self) -> str:
        s = self.stats.summary()
        lines = [
            f"avg frame: {s['avg_frame_ms']:.2f}ms",
            f"avg render: {s['avg_render_ms']:.2f}ms",
            f"avg audio: {s['avg_audio_ms']:.2f}ms",
            f"fps achieved: {s['fps_achieved']:.1f}",
            f"total frames: {s['total_frames']:.0f}",
            f"skipped frames: {s['skipped_frames']:.0f}",
        ]
        return "\n".join(lines)


def create_profiler(enabled: bool = False) -> Profiler:
    """Create a profiler instance."""
    return Profiler(enabled=enabled)