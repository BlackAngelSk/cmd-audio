#!/usr/bin/env python3
"""
Music-synced terminal hacker effect with optional popup configuration UI.

This file is now a thin wrapper around the cmd_audio package.
All logic has been moved to cmd_audio/main.py and its submodules.

Usage:
    python3 music_sync_hacker_effect.py /path/to/song.mp3
    python3 music_sync_hacker_effect.py --preset chaos --diagnostics
    python3 music_sync_hacker_effect.py --replay-file frames.jsonl.gz
    python3 music_sync_hacker_effect.py --setup-ui
    python3 -m cmd_audio /path/to/song.mp3
"""

import sys

from cmd_audio.main import main

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)