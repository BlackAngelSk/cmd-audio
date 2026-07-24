"""Render loop extracted from main.py."""

from __future__ import annotations

import random
import sys
import time
from typing import Any, Dict, List, Optional

from cmd_audio.config import (
    MISSION_PHASES,
    OPERATION_MODES,
    SCENE_PACKS,
    TARGETS,
    TERMINAL_PROFILES,
    THEMES,
    apply_theme,
    set_bar_mode,
    set_theme_mode,
    set_bass_threshold,
    CURRENT_THEME_MODE,
    BASS_THRESHOLD,
)
from cmd_audio.utils import clamp
from cmd_audio.terminal import RawInput
from cmd_audio.audio import AudioFeatures, make_demo_audio_features
from cmd_audio.effects import (
    build_banner_lines,
    meter_bar,
    make_log_line,
    make_incident_line,
    panel_box,
    prompt_banner_text,
)
from cmd_audio.visual import (
    VisualState,
    ALL_VISUAL_MODULES,
    build_telemetry_lines,
    compose_center_panel,
    generate_shell_feed,
    get_visual_modules_for_cycle,
    refresh_visual_state,
    render_paneled_visuals,
)
from cmd_audio.mission import (
    IncidentFeedState,
    maybe_apply_defender_countermeasure,
    mission_timeline_from_progress,
    should_shift_scene,
)


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