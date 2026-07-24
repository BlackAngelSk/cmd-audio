"""TUI menu system using curses (Phase 3.1)."""

from __future__ import annotations

import curses
from typing import List, Optional, Callable
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


class TUIMenu:
    """A simple curses-based TUI menu for config selection and preset browsing."""

    def __init__(self, title: str = "cmd-audio", items: Optional[List[str]] = None):
        self.title = title
        self.items = items or []
        self.selected = 0
        self.running = False
        self.result_idx: Optional[int] = None
        self.on_select: Optional[Callable[[int], None]] = None

    def run(self) -> Optional[int]:
        """Run the TUI menu and return the selected index or None."""
        try:
            return curses.wrapper(self._curses_loop)
        except Exception as e:
            logger.error("TUI menu error: %s", e)
            return None

    def _curses_loop(self, stdscr) -> Optional[int]:
        curses.curs_set(0)
        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            title = self.title[:w-4] if self.title else ""
            stdscr.addstr(1, max(0, (w - len(title)) // 2), title, curses.A_BOLD)
            stdscr.addstr(2, 0, "=" * min(w-2, len(title)+4))
            for i, item in enumerate(self.items):
                if i == self.selected:
                    stdscr.addstr(4 + i, 2, f" > {item[:w-6]}", curses.A_REVERSE)
                else:
                    stdscr.addstr(4 + i, 2, f"   {item[:w-6]}")
            stdscr.addstr(h-2, 2, "[↑/↓] Select  [Enter] Choose  [q] Quit", curses.A_DIM)
            stdscr.refresh()
            key = stdscr.getch()
            if key == ord('q') or key == 27:
                return None
            elif key == curses.KEY_UP and self.selected > 0:
                self.selected -= 1
            elif key == curses.KEY_DOWN and self.selected < len(self.items) - 1:
                self.selected += 1
            elif key in (10, 13):
                return self.selected