"""Raw terminal input handling."""

from __future__ import annotations

import os
import select
import sys
import termios
import tty
from typing import Optional


class RawInput:
    """Enable/disable raw (cbreak) mode and read single keystrokes."""

    def __init__(self) -> None:
        self.enabled = False
        self.fd: Optional[int] = None
        self.old = None

    def enable(self) -> None:
        if not sys.stdin.isatty() or os.name != "posix":
            return
        fd = sys.stdin.fileno()
        self.fd = fd
        self.old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        self.enabled = True

    def disable(self) -> None:
        if self.enabled and self.fd is not None and self.old is not None:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
        self.enabled = False

    def read_key(self) -> Optional[str]:
        if not self.enabled or self.fd is None:
            return None
        r, _, _ = select.select([sys.stdin], [], [], 0)
        if not r:
            return None
        ch = os.read(self.fd, 1)
        if not ch:
            return None
        return ch.decode("utf-8", errors="ignore")