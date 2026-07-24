"""Screen capture integration with ffmpeg (Phase 4.4)."""

from __future__ import annotations

import subprocess
import threading
from typing import Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


class ScreenCapture:
    """Captures terminal output as video using ffmpeg."""

    def __init__(self, output_path: str = "", fps: int = 30):
        self.output_path = output_path
        self.fps = fps
        self.process: Optional[subprocess.Popen] = None
        self.running = False

    def start(self) -> None:
        """Start capturing screens."""
        if not self.output_path:
            logger.error("No output path specified")
            return
        try:
            self.process = subprocess.Popen(
                [
                    "ffmpeg", "-y", "-f", "x11grab",
                    "-framerate", str(self.fps),
                    "-i", ":0.0",
                    "-vcodec", "libx264",
                    "-pix_fmt", "yuv420p",
                    self.output_path,
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.running = True
            logger.info("Started screen capture: %s", self.output_path)
        except FileNotFoundError:
            logger.error("ffmpeg not found for screen capture")
        except Exception as exc:
            logger.error("Failed to start screen capture: %s", exc)

    def stop(self) -> None:
        """Stop capturing screens."""
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                pass
            self.process = None
            logger.info("Stopped screen capture")

    def is_running(self) -> bool:
        return self.running


def start_recording(output_path: str = "recording.mp4", fps: int = 30) -> ScreenCapture:
    """Convenience function to start screen recording."""
    cap = ScreenCapture(output_path, fps)
    cap.start()
    return cap