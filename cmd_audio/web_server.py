"""Web server mode for browser-based visualization (Phase 4.1)."""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Callable, Dict, List, Optional
from http.server import HTTPServer, SimpleHTTPRequestHandler
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)

try:
    from websocket_server import WebsocketServer  # type: ignore[import-untyped]
    HAS_WS_SERVER = True
except ImportError:
    HAS_WS_SERVER = False


class AudioServer:
    """HTTP server that serves a browser-based visualization."""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.server = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.audio_data: Dict[str, Any] = {}
        self.clients: List[Any] = []
    
    def start(self) -> None:
        """Start the web server."""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        """Stop the web server."""
        self.running = False
        if self.server:
            self.server.shutdown()
    
    def _run(self) -> None:
        """Run the HTTP server."""
        try:
            from http.server import HTTPServer
            server = HTTPServer((self.host, self.port), self._make_handler())
            self.server = server
            server.serve_forever()
        except Exception as e:
            logger.error("Web server error: %s", e)
    
    def _make_handler(self) -> type:
        server = self
        class Handler(SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/":
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(self._html_page().encode())
                elif self.path == "/api/audio":
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(server.audio_data).encode())
                else:
                    super().do_GET()
            
            def _html_page(self) -> str:
                return """
<!DOCTYPE html>
<html>
<head><title>cmd-audio</title></head>
<body style="background:#000;color:#0f0;font-family:monospace;text-align:center;padding:20px;">
<h1>cmd-audio</h1>
<pre id="viz" style="font-size:14px;line-height:1.2;"></pre>
<script>
setInterval(async () => {
  try {
    const r = await fetch("/api/audio");
    const d = await r.json();
    document.getElementById('viz').textContent = JSON.stringify(d, null, 2);
  } catch(e) {}
}, 100);
</script>
</body>
</html>
"""
        return Handler
    
    def update_audio_data(self, data: Dict[str, Any]) -> None:
        """Update the audio data for streaming to clients."""
        self.audio_data = data


def start_web_server(host: str = "localhost", port: int = 8080) -> AudioServer:
    """Create and start a web server."""
    server = AudioServer(host, port)
    server.start()
    return server


def is_web_server_available() -> bool:
    """Check if the web server is available."""
    return True