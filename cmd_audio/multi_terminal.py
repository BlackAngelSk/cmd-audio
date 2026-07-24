"""Multiple terminal / tmux pane support (Phase 3.10)."""

from __future__ import annotations

import os
import subprocess
from typing import List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


def in_tmux() -> bool:
    """Check if running inside tmux."""
    return os.environ.get("TMUX", "") != ""


def create_tmux_panes(count: int = 2, cmd: str = "") -> bool:
    """Create additional tmux panes."""
    if not in_tmux():
        logger.warning("Not in tmux session")
        return False
    try:
        # Split windows and run commands
        for i in range(count - 1):
            subprocess.run(
                ["tmux", "split-window", cmd or "echo new pane"],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["tmux", "select-layout", "even-horizontal"],
                check=True,
                capture_output=True,
            )
        return True
    except Exception as exc:
        logger.error("Failed to create tmux panes: %s", exc)
        return False


def list_tmux_panes() -> List[str]:
    """List tmux pane IDs."""
    if not in_tmux():
        return []
    try:
        result = subprocess.run(
            ["tmux", "list-panes", "-F", "#{pane_index} #{pane_width}x#{pane_height}"],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except Exception:
        return []


def tmux_send_keys(pane_id: str, keys: str) -> bool:
    """Send keys to a specific tmux pane."""
    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", pane_id, keys],
            check=True,
            capture_output=True,
        )
        return True
    except Exception:
        return False


def create_rendering_copy(pane_index: int) -> bool:
    """Send panel index to a tmux pane for rendering."""
    if not in_tmux():
        return False
    return tmux_send_keys(
        f".{pane_index}",
        f"cmd-audio --panel {pane_index}",
    )