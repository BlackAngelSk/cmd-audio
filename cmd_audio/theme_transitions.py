"""Theme transition effects (Phase 2.5)."""

from __future__ import annotations

from typing import Tuple
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


class ThemeTransition:
    """Manages smooth crossfade/blend between themes."""

    def __init__(self, from_theme: Tuple[str, str, str], to_theme: Tuple[str, str, str], frames: int = 3):
        self.from_theme = from_theme
        self.to_theme = to_theme
        self.frames = max(1, frames)
        self.current_frame = 0

    def get_current_theme(self) -> Tuple[str, str, str]:
        if self.current_frame >= self.frames:
            return self.to_theme
        progress = self.current_frame / self.frames
        # Binary switch at 50% (ANSI colors cannot be interpolated)
        return self.to_theme if progress >= 0.5 else self.from_theme

    def advance_frame(self) -> bool:
        if self.current_frame < self.frames:
            self.current_frame += 1
        return self.current_frame >= self.frames

    def reset(self) -> None:
        self.current_frame = 0


def create_theme_transition(from_theme: str, to_theme: str, frames: int = 3) -> ThemeTransition:
    from cmd_audio.config import THEMES
    default = ("\033[92m", "\033[32m", "\033[2;32m")
    from_theme_colors = THEMES.get(from_theme, default)
    to_theme_colors = THEMES.get(to_theme, default)
    return ThemeTransition(from_theme_colors, to_theme_colors, frames)