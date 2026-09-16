"""Render loop extracted from main.py."""

from __future__ import annotations

import random
import sys
from typing import Any, List

from cmd_audio.audio import AudioFeatures
from cmd_audio.effects import meter_bar


class RenderLoop:
    """Manages the main rendering loop."""

    def __init__(self, args: Any, audio: AudioFeatures) -> None:
        self.args = args
        self.audio = audio
        self.running = True
        self.paused = False

    def stop(self) -> None:
        """Stop the render loop."""
        self.running = False

    def render_frame(self, frame_idx: int) -> None:
        """Render a single frame."""
        t = frame_idx / self.args.fps
        if t >= self.audio.duration:
            return

        # Simple demo frame rendering
        frame = self._build_demo_frame(t)
        sys.stdout.write("\033[H")
        sys.stdout.write("\n".join(frame))
        sys.stdout.write("\033[0m")
        sys.stdout.flush()

    def _build_demo_frame(self, t: float) -> List[str]:
        """Build a simple demo frame for rendering."""
        frame_idx = int(t * self.args.fps)
        if frame_idx >= len(self.audio.levels):
            return [""]

        level = self.audio.levels[frame_idx]
        beat = frame_idx < len(self.audio.beats) and self.audio.beats[frame_idx]

        lines = []
        lines.append(f"{'=' * 60}")
        lines.append(f"  CMD-AUDIO  [frame {frame_idx}]  level: {level:.2f}  {'*BEAT*' if beat else ''}")
        lines.append(f"{'=' * 60}")

        # Add meter bar
        bar = meter_bar(level, 50)
        lines.append(f"  Level: {bar}")

        # Add some visual elements
        for i in range(10):
            char = random.choice("|/\\-+*")
            lines.append(f"  {char * 60}")

        lines.append(f"{'=' * 60}")
        return lines


def clear_and_home() -> None:
    """Clear screen and move cursor to home position."""
    from cmd_audio.config import CLEAR
    sys.stdout.write(CLEAR)
    sys.stdout.flush()