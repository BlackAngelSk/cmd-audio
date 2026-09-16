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

import json as _json
import os
import sys
import threading
import webbrowser

from cmd_audio.main import main
from cmd_audio.control import get_browser_live_state


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
                elif self.path.startswith("/api/"):
                    self._handle_api()
                else:
                    self.send_error(404)

            def do_POST(self) -> None:
                if self.path.startswith("/api/"):
                    self._handle_api()
                else:
                    self.send_error(404)

            def do_OPTIONS(self) -> None:
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def _handle_api(self) -> None:
                """Handle /api/* requests directly using the shared live state."""
                method = self.command
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length) if content_length > 0 else b""
                data = {}
                if body:
                    try:
                        data = _json.loads(body.decode())
                    except Exception:
                        self._send_json(400, {"status": "error", "message": "Invalid JSON"})
                        return

                live = get_browser_live_state()

                # /api/music — POST {url: ...}
                if self.path == "/api/music" and method == "POST":
                    music_url = data.get("url", "").strip()
                    if not music_url:
                        self._send_json(200, {"status": "error", "message": "No URL provided"})
                        return
                    if live is not None:
                        live.request_music_change(music_url)
                        self._send_json(200, {"status": "ok", "message": "Music change requested"})
                    else:
                        self._send_json(200, {
                            "status": "error",
                            "message": "Live state not available yet – "
                            "wait for CMD-AUDIO to finish starting.",
                        })
                    return

                # /api/config — GET
                if self.path == "/api/config" and method == "GET":
                    self._send_json(200, live.to_dict() if live is not None else {})
                    return

                # /api/audio — GET
                if self.path == "/api/audio" and method == "GET":
                    self._send_json(200, {})
                    return

                self._send_json(404, {"status": "error", "message": "Unknown endpoint"})

            def _send_json(self, status: int, data: dict) -> None:
                payload = _json.dumps(data).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(payload)

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
