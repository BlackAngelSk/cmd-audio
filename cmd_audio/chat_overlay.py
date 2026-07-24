"""Chat overlay for IRC/Discord messages (Phase 4.8)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ChatMessage:
    author: str
    text: str
    timestamp: float
    platform: str = "irc"


class ChatOverlay:
    """Manages a chat overlay for displaying messages alongside visualization."""

    def __init__(self, max_messages: int = 10) -> None:
        self.messages: List[ChatMessage] = []
        self.max_messages = max_messages

    def add_message(self, author: str, text: str, timestamp: float, platform: str = "irc") -> None:
        msg = ChatMessage(author=author, text=text, timestamp=timestamp, platform=platform)
        self.messages.append(msg)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def render(self, width: int = 60) -> List[str]:
        if not self.messages:
            return []
        lines: List[str] = []
        for msg in self.messages[-5:]:
            line = f"[{msg.platform}] {msg.author}: {msg.text[:width-20]}"
            lines.append(line)
        return lines

    def clear(self) -> None:
        self.messages.clear()