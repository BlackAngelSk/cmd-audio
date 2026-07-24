"""Volume/gain normalization (Phase 2.3)."""

from __future__ import annotations

import math
from typing import List
from cmd_audio.utils import clamp
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


class VolumeNormalizer:
    """Adaptive volume normalization with gain adjustment."""

    def __init__(self, target_rms_db: float = -20.0, lookahead_ms: float = 50.0, history_len: int = 30):
        self.target_rms_db = target_rms_db
        self.lookahead_ms = lookahead_ms
        self.history_len = history_len
        self.gain_history: List[float] = []

    def compute_gain(self, rms: float) -> float:
        """Compute the gain needed to normalize audio to target level."""
        if rms <= 0.0:
            return 1.0
        # Target RMS from dB
        import math
        target_rms = 10 ** (self.target_rms_db / 20.0)
        gain = target_rms / rms
        gain = clamp(gain, 0.01, 100.0)
        self.gain_history.append(gain)
        if len(self.gain_history) > self.history_len:
            self.gain_history.pop(0)
        # Smooth gain
        avg = sum(self.gain_history) / len(self.gain_history) if self.gain_history else 1.0
        return clamp(avg, 0.01, 100.0)

    def apply(self, samples: List[float], gain: float) -> List[float]:
        """Apply gain to samples."""
        return [s * gain for s in samples]


def normalize_volume(samples: List[float], target_db: float = -20.0) -> List[float]:
    """Normalize samples to target dB level."""
    if not samples:
        return []
    rms = math.sqrt(sum(s**2 for s in samples) / len(samples)) if samples else 0.0
    if rms <= 0.0:
        return samples
    target_rms = 10 ** (target_db / 20.0)
    gain = target_rms / rms
    gain = clamp(gain, 0.01, 100.0)
    return [s * gain for s in samples]