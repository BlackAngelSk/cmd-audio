"""REST API for controlling visualization (Phase 4.7)."""

from __future__ import annotations

import json
import threading
from typing import Any, Callable, Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


class RESTAPIHandler(BaseHTTPRequestHandler):
    """HTTP REST API handler for cmd-audio control."""
    
    api_handler: Optional[Callable] = None
    
    def do_GET(self) -> None:
        self._handle_request("GET")
    
    def do_POST(self) -> None:
        self._handle_request("POST")
    
    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def _handle_request(self, method: str) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b""
            data = json.loads(body) if body else {}
            
            if RESTAPIHandler.api_handler:
                result = RESTAPIHandler.api_handler(method, self.path, data)
            else:
                result = {"error": "No handler configured"}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as exc:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}).encode())
    
    def log_message(self, format: str, *args: Any) -> None:
        logger.debug("API: %s", format % args)


class RESTAPIServer:
    """REST API server for controlling the visualization."""
    
    def __init__(self, host: str = "localhost", port: int = 8081):
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.control_state: Dict[str, Any] = {}
    
    def start(self) -> None:
        self.running = True
        RESTAPIHandler.api_handler = self._handle_api
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        self.running = False
        if self.server:
            self.server.shutdown()
    
    def _run(self) -> None:
        try:
            self.server = HTTPServer((self.host, self.port), RESTAPIHandler)
            self.server.serve_forever()
        except Exception as e:
            logger.error("REST API server error: %s", e)
    
    def _handle_api(self, method: str, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if path == "/api/status":
            return {"status": "running", "state": self.control_state}
        elif path == "/api/theme":
            if method == "POST":
                self.control_state["theme"] = data.get("theme", "matrix")
                return {"theme": self.control_state["theme"]}
        elif path == "/api/audio":
            return self.control_state.get("audio_features", {})
        elif path == "/api/commands":
            if method == "POST":
                cmd = data.get("command", "")
                return {"received": cmd}
        return {"error": "Unknown endpoint"}
    
    def update_state(self, state: Dict[str, Any]) -> None:
        self.control_state.update(state)