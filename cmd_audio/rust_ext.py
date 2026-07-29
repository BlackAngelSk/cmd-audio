"""Rust/C extension for audio processing (Phase 5.1)."""

from __future__ import annotations

import os
import sys
import subprocess
from typing import Any, List, Optional, Sequence
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)

HAS_RUST = False

try:
    import cmd_audio._rust_core as rust_core  # type: ignore[import-untyped]
    HAS_RUST = True
except ImportError:
    rust_core = None  # type: ignore[assignment]


def is_rust_available() -> bool:
    return HAS_RUST


def build_rust_extension() -> bool:
    """Build Rust extension using maturin or cargo."""
    ext_dir = os.path.join(os.path.dirname(__file__), "rust")
    if not os.path.isdir(ext_dir):
        logger.warning("Rust extension directory not found: %s", ext_dir)
        return False
    try:
        result = subprocess.run(
            ["maturin", "build", "--release"],
            cwd=ext_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("Rust extension built successfully")
            return True
        logger.error("Rust build failed: %s", result.stderr)
        return False
    except FileNotFoundError:
        logger.error("maturin not found")
        return False


def fft_rust(samples: Sequence[float], sample_rate: int) -> List[float]:
    """Perform FFT using Rust extension if available."""
    if HAS_RUST and rust_core is not None:
        return rust_core.fft(list(samples), sample_rate)
    # Fallback to pure Python — compute Goertzel power for each frequency band
    from cmd_audio.config import FREQ_CENTERS
    from cmd_audio.audio import goertzel_power
    return [goertzel_power([int(s) for s in samples], sample_rate, f) for f in FREQ_CENTERS]


def goertzel_rust(samples: Sequence[float], sample_rate: int, freq: float) -> float:
    """Perform Goertzel algorithm using Rust extension if available."""
    if HAS_RUST and rust_core is not None:
        return rust_core.goertzel(list(samples), sample_rate, freq)
    from cmd_audio.audio import goertzel_power  # type: ignore[import-untyped]
    return goertzel_power([int(s) for s in samples], sample_rate, freq)  # type: ignore[arg-type]
