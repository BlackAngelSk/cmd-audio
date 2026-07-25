#!/usr/bin/env python3
"""
Music-synced terminal hacker effect with browser-based Live Controls.

Usage:
    python3 music_sync_hacker_effect.py /path/to/song.mp3
    python3 music_sync_hacker_effect.py --preset chaos --diagnostics
    python3 music_sync_hacker_effect.py --replay-file frames.jsonl.gz
    python3 music_sync_hacker_effect.py --setup-ui
    python3 -m cmd_audio /path/to/song.mp3
"""

import os
import sys
import threading
import webbrowser

from cmd_audio.main import main


def _open_live_controls_in_browser() -> None:
    """Start a local HTTP server and open the Live Controls HTML in the default browser."""
    try:
        from http.server import HTTPServer, SimpleHTTPRequestHandler

        project_root = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(project_root, "live_controls.html")
        if not os.path.exists(html_path):
            return

        host = "localhost"
        port = 8765

        class _Handler(SimpleHTTPRequestHandler):
            def do_GET(self) -> None:
                if self.path == "/" or self.path == "/live-controls":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    with open(html_path, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self.send_error(404)

            def log_message(self, format: str, *args) -> None:
                pass  # suppress request logging

        server = HTTPServer((host, port), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        url = f"http://{host}:{port}"
        print(f"  Live Controls: {url}")

        try:
            webbrowser.open(url)
        except Exception:
            pass
    except Exception:
        pass


if __name__ == "__main__":
    # Open live controls in browser
    _open_live_controls_in_browser()

    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
