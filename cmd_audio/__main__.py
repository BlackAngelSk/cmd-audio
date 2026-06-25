"""Allow running as ``python -m cmd_audio``."""

from __future__ import annotations

import sys

from cmd_audio.main import main

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)