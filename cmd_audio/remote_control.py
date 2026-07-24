"""Remote control via socket/IPC (Phase 3.8)."""

from __future__ import annotations

import json
import os
import socket
import threading
from typing import Any, Callable, Dict, List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)

SOCKET_PATH = os.path.expanduser("~/.config/cmd-audio/remote.sock")


class RemoteControlServer:
    """Unix socket / TCP server for external commands."""

    def __init__(self, socket_path: str = SOCKET_PATH, tcp_port: int = 0):
        self.socket_path = socket_path
        self.tcp_port = tcp_port
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._server: Optional[socket.socket] = None
        self.command_handler: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None

    def start(self) -> None:
        self.running = True
        os.makedirs(os.path.dirname(self.socket_path), exist_ok=True)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.running = False
        if self._server:
            try:
                self._server.close()
            except Exception:
                pass
        try:
            os.unlink(self.socket_path)
        except OSError:
            pass

    def _run(self) -> None:
        try:
            self._server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._server.bind(self.socket_path)
            self._server.listen(5)
            self._server.settimeout(1.0)
            while self.running:
                try:
                    conn, _ = self._server.accept()
                    threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
                except socket.timeout:
                    continue
                except OSError:
                    break
        except Exception as e:
            logger.error("Remote control error: %s", e)

    def _handle_client(self, conn: socket.socket) -> None:
        try:
            data = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
                if b"\n" in data:
                    break
            if data:
                msg = json.loads(data.decode().strip())
                if self.command_handler:
                    result = self.command_handler(msg.get("command", ""), msg)
                else:
                    result = {"error": "No handler"}
                conn.sendall(json.dumps(result).encode() + b"\n")
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass


def create_remote_control(socket_path: str = SOCKET_PATH) -> RemoteControlServer:
    return RemoteControlServer(socket_path)