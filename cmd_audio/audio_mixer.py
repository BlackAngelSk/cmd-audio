"""Multiple audio source mixing (Phase 5.3)."""

from __future__ import annotations

from typing import Any, List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


def mix_sources(a: List[float], b: List[float], balance: float = 0.5) -> List[float]:
    """Mix two audio sample buffers with a given balance."""
    length = min(len(a), len(b))
    b_clamped = max(0.0, min(1.0, balance))
    return [a[i] * (1.0 - b_clamped) + b[i] * b_clamped for i in range(length)]


def mix_multiple_sources(sources: List[List[float]], weights: Optional[List[float]] = None) -> List[float]:
    """Mix multiple audio sources with optional weights."""
    if not sources:
        return []
    if weights is None:
        weights = [1.0 / len(sources)] * len(sources)
    if len(sources) != len(weights):
        raise ValueError("Must have same number of sources and weights")
    max_len = max(len(s) for s in sources)
    result = [0.0] * max_len
    for i, (source, weight) in enumerate(zip(sources, weights)):
        for j in range(len(source)):
            result[j] += source[j] * weight
    return result


def apply_crossfade(a: List[float], b: List[float], fade_duration: int = 0) -> List[float]:
    """Apply a crossfade between two audio sources."""
    if not a and not b:
        return []
    length = max(len(a), len(b))
    result = [0.0] * length
    for i in range(length):
        if i < fade_duration:
            weight = i / fade_duration
            val = (a[i] if i < len(a) else 0.0) * (1.0 - weight)
            val += (b[i] if i < len(b) else 0.0) * weight
            result[i] = val
        else:
            result[i] = b[i] if i < len(b) else 0.0
    return result