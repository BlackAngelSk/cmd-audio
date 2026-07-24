"""Network trigger mode (Phase 4.9)."""

from __future__ import annotations

import json
import socket
import threading
from typing import Any, Callable, Dict, List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


class NetworkTrigger:
    """Visuals triggered by network events (webhook or packet capture)."""

    def __init__(self, port: int = 9998) -> None:
        self.port = port
        self.running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._server: Optional[socket.socket] = None
        self.on_trigger: Optional[Callable[[Dict[str, Any]], None]] = None

    def start(self) -> None:
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.running = False
        if self._server:
            try:
                self._server.close()
            except Exception:
                pass

    def _run(self) -> None:
        try:
            self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server.bind(("0.0.0.0", self.port))
            self._server.listen(5)
            self._server.settimeout(2.0)
            while self.running:
                try:
                    conn, addr = self._server.accept()
                    threading.Thread(target=self._handler, args=(conn,), daemon=True).start()
                except socket.timeout:
                    continue
        except Exception as e:
            logger.error("Network trigger error: %s", e)

    def _handler(self, conn: socket.socket) -> None:
        try:
            data = b""
            while True:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                data += chunk
                if b"\n" in data:
                    break
            if data:
                try:
                    msg = json.loads(data.decode().strip())
                    if self.on_trigger:
                        self.on_trigger(msg)
                    result = json.dumps({"status": "ok"}).encode() + b"\n"
                    conn.sendall(result)
                except json.JSONDecodeError:
                    conn.sendall(b'{"error":"invalid json"}\n')
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass


def create_network_trigger(port: int = 9998) -> NetworkTrigger:
    return NetworkTrigger(port)