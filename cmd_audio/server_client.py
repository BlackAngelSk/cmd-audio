"""Server/client mode (Phase 4.5)."""

from __future__ import annotations

import json
import socket
import threading
from typing import Any, Callable, Dict, List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


class AudioServer:
    """Server that does audio analysis and dispatches data to clients."""

    def __init__(self, host: str = "localhost", port: int = 9999):
        self.host = host
        self.port = port
        self.clients: List[socket.socket] = []
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._server: Optional[socket.socket] = None
        self.on_audio_data: Optional[Callable[[], Dict[str, Any]]] = None

    def start(self) -> None:
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.running = False
        if self._server:
            self._server.close()
        for client in self.clients:
            try:
                client.close()
            except Exception:
                pass
        self.clients.clear()

    def _run(self) -> None:
        try:
            self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server.bind((self.host, self.port))
            self._server.listen(5)
            self._server.settimeout(1.0)
            while self.running:
                try:
                    conn, addr = self._server.accept()
                    self.clients.append(conn)
                    threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
                except socket.timeout:
                    continue
        except Exception as e:
            logger.error("Audio server error: %s", e)

    def _handle_client(self, conn: socket.socket) -> None:
        while self.running:
            try:
                if self.on_audio_data:
                    data = self.on_audio_data()
                    msg = json.dumps(data).encode() + b"\n"
                    conn.sendall(msg)
                conn.settimeout(1.0)
            except (socket.timeout, ConnectionError):
                break
        try:
            conn.close()
        except Exception:
            pass
        if conn in self.clients:
            self.clients.remove(conn)

    def broadcast(self, data: Dict[str, Any]) -> None:
        msg = json.dumps(data).encode() + b"\n"
        dead: List[socket.socket] = []
        for client in self.clients:
            try:
                client.sendall(msg)
            except Exception:
                dead.append(client)
        for client in dead:
            if client in self.clients:
                self.clients.remove(client)


class AudioClient:
    """Client that connects to a server and receives audio data."""

    def __init__(self, host: str = "localhost", port: int = 9999):
        self.host = host
        self.port = port
        self._socket: Optional[socket.socket] = None
        self.running = False

    def connect(self) -> bool:
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.host, self.port))
            self.running = True
            return True
        except Exception as exc:
            logger.error("Client connection failed: %s", exc)
            return False

    def disconnect(self) -> None:
        self.running = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass

    def receive(self) -> Dict[str, Any]:
        if not self._socket:
            return {}
        try:
            self._socket.settimeout(1.0)
            data = b""
            while True:
                chunk = self._socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                if b"\n" in data:
                    break
            if data:
                return json.loads(data.decode().strip())
        except (socket.timeout, ConnectionError):
            pass
        return {}