"""Notification system (Phase 3.7)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional
import cmd_audio.config as _cfg


@dataclass
class ToastNotification:
    """A single notification toast."""
    message: str
    timestamp: float
    level: str = "info"  # info, warn, error
    ttl: float = 3.0
    visible: bool = True


class NotificationManager:
    """Manages toast-style notifications at the bottom of the screen."""

    def __init__(self, ttl: float = 3.0):
        self.notifications: List[ToastNotification] = []
        self.ttl = ttl
        self.onclick_callback = None

    def notify(self, message: str, level: str = "info", ttl: Optional[float] = None) -> None:
        """Send a notification."""
        n = ToastNotification(
            message=message,
            timestamp=time.time(),
            level=level,
            ttl=ttl or self.ttl
        )
        self.notifications.append(n)

    def update(self) -> List[ToastNotification]:
        """Update notifications and remove expired ones."""
        now = time.time()
        active: List[ToastNotification] = []
        for n in self.notifications:
            if now - n.timestamp <= n.ttl:
                active.append(n)
        self.notifications = active
        return active

    def render(self, width: int) -> List[str]:
        """Render active notifications."""
        self.update()
        if not self.notifications:
            return []
        lines: List[str] = []
        for n in self.notifications[-1:]:  # Only show the most recent
            elapsed = time.time() - n.timestamp
            progress = elapsed / n.ttl if n.ttl > 0 else 1.0
            bar_w = max(0, int((1.0 - progress) * width))
            bar = "█" * bar_w + "░" * (width - bar_w)
            color = _cfg.GREEN_BRIGHT if n.level == "info" else (_cfg.STATUS_CRIT if n.level == "error" else _cfg.STATUS_WARN)
            icon = "●" if n.level == "info" else ("!" if n.level == "warn" else "✗")
            lines.append(f"{color}  {icon} {n.message}{_cfg.RESET}")
            lines.append(f"{_cfg.GREEN_DIM}  {bar}{_cfg.RESET}")
        return lines

    def clear(self) -> None:
        """Clear all notifications."""
        self.notifications.clear()


def notify(manager: NotificationManager, message: str, level: str = "info") -> None:
    """Convenience function to send a notification."""
    manager.notify(message, level)