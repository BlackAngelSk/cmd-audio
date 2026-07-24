"""Collaborative mode (Phase 5.9)."""

from __future__ import annotations

import json
import threading
from typing import Any, Callable, Dict, List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


class CollaborativeSession:
    """Multiple users connect to a shared visualization session."""

    def __init__(self, host: str = "localhost", port: int = 9997):
        self.host = host
        self.port = port
        self.clients: List[str] = []
        self.user_states: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.lock = threading.Lock()
        self.on_command: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None

    def add_user(self, user_id: str) -> None:
        with self.lock:
            self.clients.append(user_id)
            self.user_states[user_id] = {"theme": "matrix", "sensitivity": 1.0}

    def remove_user(self, user_id: str) -> None:
        with self.lock:
            if user_id in self.clients:
                self.clients.remove(user_id)
            self.user_states.pop(user_id, None)

    def get_state(self, user_id: str) -> Dict[str, Any]:
        with self.lock:
            return dict(self.user_states.get(user_id, {}))

    def update_state(self, user_id: str, state: Dict[str, Any]) -> None:
        with self.lock:
            if user_id not in self.user_states:
                self.user_states[user_id] = {}
            self.user_states[user_id].update(state)

    def list_users(self) -> List[str]:
        with self.lock:
            return list(self.clients)

    def broadcast_state(self) -> Dict[str, Any]:
        with self.lock:
            return dict(self.user_states)


def create_collaborative_session(host: str = "localhost", port: int = 9997) -> CollaborativeSession:
    return CollaborativeSession(host, port)