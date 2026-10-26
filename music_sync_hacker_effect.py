#!/usr/bin/env python3
"""
Music-synced terminal hacker effect with browser-based Live Controls.

Usage:
    ./start.sh /path/to/song.mp3 --web
    python3 music_sync_hacker_effect.py /path/to/song.mp3 --web
    python3 music_sync_hacker_effect.py --preset chaos --diagnostics
    python3 music_sync_hacker_effect.py --replay-file frames.jsonl.gz
    python3 music_sync_hacker_effect.py --setup-ui
    python3 -m cmd_audio /path/to/song.mp3
"""

import sys
import webbrowser

from cmd_audio.main import main


def _start_browser_controls(open_browser: bool = True) -> None:
    """Serve the live-controls page from the *real* backend.

    This used to spin up a throw-away static server on port 8765 that only knew
    about /api/music and /api/config -- every slider and checkbox on the page
    posted to /api/live, got a 404 and silently did nothing.
    """
    try:
        from cmd_audio.web_server import start_web_server
    except Exception as exc:  # pragma: no cover - import guard
        print(f"  Live Controls unavailable: {exc}", file=sys.stderr)
        return

    try:
        server = start_web_server(host="localhost", port=8080, live_on_root=True)
    except Exception as exc:  # pragma: no cover - bind guard
        print(f"  Live Controls unavailable: {exc}", file=sys.stderr)
        return

    if server is None or server.server is None:
        print(
            f"  Live Controls unavailable: {server.bind_error if server else 'unknown error'}",
            file=sys.stderr,
        )
        return

    url = f"http://localhost:{server.port}"
    print(f"\n  Live Controls: {url}\n")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass


if __name__ == "__main__":
    if "--web" in sys.argv or "--setup-ui" in sys.argv:
        # main() starts the server itself in those modes; just don't crash here.
        pass
    else:
        _start_browser_controls()

    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
