"""WebAssembly build support (Phase 5.7)."""

from __future__ import annotations

import os
import subprocess
from typing import List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


def build_wasm() -> bool:
    """Build WebAssembly version of the visualization."""
    try:
        result = subprocess.run(
            ["cargo", "build", "--target", "wasm32-unknown-emscripten", "--release"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("WASM build successful")
            return True
        logger.error("WASM build failed: %s", result.stderr)
        return False
    except FileNotFoundError:
        logger.error("cargo not found")
        return False


def get_wasm_output_path() -> str:
    return os.path.join("target", "wasm32-unknown-emscripten", "release")