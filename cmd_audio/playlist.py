"""Playlist management (Phase 3.2)."""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from typing import List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Playlist:
    """Manages a playlist of audio files."""
    tracks: List[str] = field(default_factory=list)
    index: int = -1
    shuffle: bool = False
    repeat_mode: str = "none"  # "none", "single", "all"
    _shuffle_order: List[int] = field(default_factory=list)

    def load(self, path: str) -> None:
        """Load tracks from a text file (one per line)."""
        self.tracks.clear()
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if os.path.exists(line):
                    self.tracks.append(line)
        self.index = -1

    def current_track(self) -> Optional[str]:
        """Return the current track or None."""
        if self.index < 0 or self.index >= len(self.tracks):
            return None
        return self.tracks[self.index]

    def next_track(self) -> Optional[str]:
        """Advance to the next track."""
        if not self.tracks:
            return None
        if self.shuffle:
            if not self._shuffle_order:
                self._shuffle_order = list(range(len(self.tracks)))
                random.shuffle(self._shuffle_order)
            try:
                pos = self._shuffle_order.index(self.index)
            except ValueError:
                pos = 0
            next_pos = (pos + 1) % len(self._shuffle_order)
            self.index = self._shuffle_order[next_pos]
        else:
            self.index += 1
            if self.index >= len(self.tracks):
                if self.repeat_mode == "all":
                    self.index = 0
                else:
                    return None
        return self.current_track()

    def prev_track(self) -> Optional[str]:
        """Go to the previous track."""
        if not self.tracks:
            return None
        self.index -= 1
        if self.index < 0:
            if self.repeat_mode == "all":
                self.index = len(self.tracks) - 1
            else:
                self.index = 0
        return self.current_track()

    def advance(self, step: int = 1) -> bool:
        """Advance by step tracks. Returns False if unable to advance."""
        if not self.tracks:
            return False
        if step > 0:
            for _ in range(step):
                if self.next_track() is None:
                    return False
        elif step < 0:
            for _ in range(-step):
                if self.prev_track() is None:
                    return False
        return True

    def shuffle_enable(self) -> None:
        self.shuffle = True
        self._shuffle_order = list(range(len(self.tracks)))
        random.shuffle(self._shuffle_order)

    def shuffle_disable(self) -> None:
        self.shuffle = False
        self._shuffle_order.clear()

    def set_repeat(self, mode: str) -> None:
        if mode in ("none", "single", "all"):
            self.repeat_mode = mode

    def list_tracks(self) -> List[str]:
        return list(self.tracks)


def load_playlist_file(path: str) -> Playlist:
    """Create and load a playlist from a file."""
    pl = Playlist()
    pl.load(path)
    return pl