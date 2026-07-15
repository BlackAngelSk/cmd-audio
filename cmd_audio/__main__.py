"""Allow running as ``python -m cmd_audio``."""

from __future__ import annotations

import sys

from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)

from cmd_audio.main import main

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        logger.warning("Interrupted.")
        raise SystemExit(130)
