"""Keyboard shortcuts help overlay (Phase 3.3)."""

from __future__ import annotations

from typing import List, Tuple
import cmd_audio.config as _cfg
from cmd_audio.effects import panel_box
from cmd_audio.utils import fit_text


SHORTCUTS: List[Tuple[str, str]] = [
    ("q", "Quit visualization"),
    ("p", "Pause/Resume"),
    ("+", "Increase sensitivity"),
    ("-", "Decrease sensitivity"),
    ("[", "Decrease speed"),
    ("]", "Increase speed"),
    ("t", "Cycle themes"),
    ("b", "Backward (replay)"),
    ("e", "Export frame"),
    ("c", "Toggle center panel"),
    ("v", "Cycle visual modules"),
    ("x", "Toggle extended view"),
    ("m", "Toggle menu"),
    ("r", "Toggle recording"),
    ("z", "Toggle mission timeline"),
    ("0", "Reset to defaults"),
    ("n", "Next track"),
    ("u", "Toggle UI overlay"),
    ("1", "Switch terminal mode (mainframe)"),
    ("2", "Switch terminal mode (router)"),
    ("3", "Switch terminal mode (proxy)"),
    ("a", "Toggle alert tones"),
    ("y", "Toggle audio FX"),
    ("k", "Toggle keyboard help"),
    ("j", "Cycle mission phases"),
    ("g", "Toggle defender AI"),
    ("h", "Toggle heading/status"),
    ("o", "Toggle operation mode"),
    ("l", "Toggle log feed"),
    ("w", "Toggle weighting/scene pack"),
    ("d", "Toggle diagnostics"),
    ("D", "Toggle live debug info"),
]


def render_keyboard_help(width: int, height: int) -> List[str]:
    """Render the keyboard shortcuts overlay."""
    lines: List[str] = []
    lines.append(f"{_cfg.GREEN_BRIGHT}{'=' * width}{_cfg.RESET}")
    lines.append(f"{_cfg.GREEN_BRIGHT}  KEYBOARD SHORTCUTS{_cfg.RESET}")
    lines.append(f"{_cfg.GREEN_BRIGHT}{'=' * width}{_cfg.RESET}")
    line_w = max(10, width - 4)
    for key, desc in SHORTCUTS:
        line = f"  [{key:>2}] {desc}"
        lines.append(fit_text(line, line_w))
    lines.append(f"{_cfg.GREEN_BRIGHT}{'=' * width}{_cfg.RESET}")
    lines.append(f"{_cfg.GREEN_DIM}Press any key to dismiss.{_cfg.RESET}")
    while len(lines) < height:
        lines.insert(len(lines) - 1, "")
    return lines[:height]