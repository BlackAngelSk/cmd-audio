"""Audio management extracted from main.py."""

from __future__ import annotations

import os
import subprocess
from typing import Optional

from cmd_audio.audio import AudioFeatures, read_audio_features, make_demo_audio_features
from cmd_audio.audio_input import prepare_audio_input, is_youtube_url
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


class AudioManager:
    """Manages audio loading, playback, and switching."""

    def __init__(self) -> None:
        self.player: Optional[subprocess.Popen] = None
        self.audio: Optional[AudioFeatures] = None
        self.wav_input: str = ""
        self.playback_input: str = ""
        self.cleanup_wav: bool = False
        self.audio_path: str = ""

    def load_file(self, path: str, fps: int, play: bool = True) -> None:
        """Load an audio file and prepare for playback."""
        try:
            wav_input, playback_input, cleanup_wav = prepare_audio_input(path, path)
            self.audio = read_audio_features(wav_input, fps)
            self.wav_input = wav_input
            self.playback_input = playback_input
            self.cleanup_wav = cleanup_wav
            self.audio_path = path
        except Exception as exc:
            logger.error("Audio load failed: %s", exc)
            raise

    def load_demo(self, fps: int, seconds: int = 180) -> None:
        """Load demo audio features."""
        self.audio = make_demo_audio_features(fps, seconds=seconds)
        self.audio_path = "(demo mode)"

    def start_playback(self) -> None:
        """Start audio playback if possible."""
        if self.playback_input and self.player is None:
            self.player = launch_player(self.playback_input)

    def stop_playback(self) -> None:
        """Stop audio playback."""
        if self.player is not None:
            try:
                self.player.terminate()
            except Exception:
                pass
            self.player = None

    def cleanup(self) -> None:
        """Clean up temporary files and stop playback."""
        self.stop_playback()
        if self.cleanup_wav and self.wav_input:
            try:
                os.unlink(self.wav_input)
            except OSError:
                pass

    def switch_file(self, new_path: str, fps: int, play: bool = True) -> None:
        """Switch to a new audio file."""
        self.stop_playback()
        self.cleanup()
        self.load_file(new_path, fps, play)
        self.start_playback()


def launch_player(path: str) -> Optional[subprocess.Popen]:
    """Launch an audio player."""
    import shutil
    players = [
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", path],
        ["aplay", path],
    ]
    for cmd in players:
        try:
            return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            continue
    return None