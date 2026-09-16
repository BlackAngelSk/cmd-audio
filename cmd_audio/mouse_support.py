"""Mouse support for terminal UI elements (Phase 3.9)."""

from __future__ import annotations

import sys
import os
from typing import Optional, Tuple, Callable
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


class MouseSupport:
    """Enable mouse click handling for UI elements in the terminal."""

    def __init__(self) -> None:
        self.enabled = False
        self.last_click: Optional[Tuple[int, int]] = None
        self.callback: Optional[Callable[[int, int], None]] = None

    def enable(self) -> None:
        """Enable mouse tracking in the terminal."""
        if self.enabled:
            return
        # Enable mouse tracking: \033[?1000h
        sys.stdout.write("\033[?1000h")
        sys.stdout.write("\033[?1003h")
        sys.stdout.flush()
        self.enabled = True

    def disable(self) -> None:
        """Disable mouse tracking in the terminal."""
        if not self.enabled:
            return
        sys.stdout.write("\033[?1000l")
        sys.stdout.write("\033[?1003l")
        sys.stdout.flush()
        self.enabled = False

    def parse_mouse_event(self, data: bytes) -> Optional[Tuple[int, int]]:
        """Parse a mouse event from raw terminal input."""
        if not data:
            return None
        # Button press: ESC [ M Cx Cy
        if len(data) >= 6 and data[0:3] == b'\x1b[' and data[3:4] == b'M':
            button = data[4] - 32
            x = data[5] - 32
            y = data[6] - 32 if len(data) >= 7 else 0
            if button <= 2:  # Left, middle, right click
                self.last_click = (x, y)
                return (x, y)
        return None

    def handle_click(self, x: int, y: int) -> Optional[str]:
        """Handle a mouse click. Returns an action string."""
        if self.callback:
            self.callback(x, y)
        # Simple click zone handling
        if y <= 3:
            return "header"
        elif y <= 10:
            return "main"
        else:
            return "footer"

    def __enter__(self) -> "MouseSupport":
        self.enable()
        return self

    def __exit__(self, *args) -> None:
        self.disable()


def enable_mouse_tracking() -> None:
    """Enable mouse tracking in the terminal."""
    sys.stdout.write("\033[?1000h")
    sys.stdout.write("\033[?1003h")
    sys.stdout.flush()


def disable_mouse_tracking() -> None:
    """Disable mouse tracking in the terminal."""
    sys.stdout.write("\033[?1000l")
    sys.stdout.write("\033[?1003l")
    sys.stdout.flush()