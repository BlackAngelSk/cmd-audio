"""Input handling extracted from main.py."""

from __future__ import annotations

import sys
from typing import Optional

from cmd_audio.terminal import RawInput


class InputHandler:
    """Manages keyboard input for the visualization."""

    def __init__(self) -> None:
        self.raw: Optional[RawInput] = None

    def enable(self) -> None:
        """Enable raw input mode."""
        self.raw = RawInput()
        self.raw.enable()

    def disable(self) -> None:
        """Disable raw input mode."""
        if self.raw is not None:
            self.raw.disable()
            self.raw = None

    def read_key(self) -> str:
        """Read a single key press."""
        if self.raw is None:
            return ""
        result = self.raw.read_key()
        return result if result is not None else ""

    def __enter__(self) -> "InputHandler":
        self.enable()
        return self

    def __exit__(self, *args: object) -> None:
        self.disable()