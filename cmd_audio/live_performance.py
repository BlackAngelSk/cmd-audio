"""Live performance mode (Phase 5.5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class MIDIEvent:
    channel: int
    note: int
    velocity: int
    status: str = "note_on"


@dataclass
class LivePerformanceConfig:
    """Configuration for live performance mode."""
    bpm: int = 120
    beat_sync: bool = True
    midi_enabled: bool = False
    midi_port: int = 0
    trigger_zones: List[Dict[str, Any]] = field(default_factory=list)


class LivePerformanceMode:
    """Dedicated mode for live DJ/performer use with triggers, beat sync, and MIDI."""

    def __init__(self, bpm: int = 120) -> None:
        self.bpm = bpm
        self.beat_sync = True
        self.midi_enabled = False
        self.triggers: Dict[str, Callable] = {}
        self.beat_count: int = 0
        self.running: bool = False

    def start(self) -> None:
        self.running = True
        logger.info("Live performance mode started")

    def stop(self) -> None:
        self.running = False

    def register_trigger(self, name: str, callback: Callable) -> None:
        self.triggers[name] = callback

    def on_beat(self) -> None:
        self.beat_count += 1
        for name, cb in self.triggers.items():
            try:
                cb(self.beat_count)
            except Exception as e:
                logger.error("Trigger error %s: %s", name, e)

    def send_midi(self, note: int, velocity: int = 127) -> None:
        if not self.midi_enabled:
            return
        logger.debug("MIDI: note=%d vel=%d", note, velocity)

    def set_bpm(self, bpm: int) -> None:
        self.bpm = max(20, min(300, bpm))

    def get_tempo(self) -> float:
        return 60.0 / self.bpm