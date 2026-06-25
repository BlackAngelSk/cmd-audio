"""Audio input handling: file conversion, microphone/system capture, YouTube."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from typing import Tuple


def ensure_wav_input(audio_path: str, keep_converted: bool = False) -> Tuple[str, bool]:
    """Convert non-WAV input to WAV via ffmpeg. Returns (path, needs_cleanup)."""
    if audio_path.lower().endswith(".wav"):
        return audio_path, False

    tmp = tempfile.NamedTemporaryFile(prefix="hacker_sync_", suffix=".wav", delete=False)
    tmp_wav = tmp.name
    tmp.close()

    cmd = ["ffmpeg", "-y", "-i", audio_path, "-ac", "1", "-ar", "44100", tmp_wav]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except FileNotFoundError as exc:
        try:
            os.unlink(tmp_wav)
        except OSError:
            pass
        raise RuntimeError("Non-WAV input needs ffmpeg installed") from exc
    except subprocess.CalledProcessError as exc:
        try:
            os.unlink(tmp_wav)
        except OSError:
            pass
        raise RuntimeError("ffmpeg failed to convert input audio") from exc

    if keep_converted:
        print(f"Converted audio saved to: {tmp_wav}", file=sys.stderr)
        return tmp_wav, False
    return tmp_wav, True


def capture_to_wav(source: str, seconds: int) -> str:
    """Capture mic or system audio to a temporary WAV file."""
    tmp = tempfile.NamedTemporaryFile(prefix=f"hacker_{source}_", suffix=".wav", delete=False)
    wav_out = tmp.name
    tmp.close()

    if source == "mic":
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-f", "pulse", "-i", "default",
            "-t", str(seconds), "-ac", "1", "-ar", "44100", wav_out,
        ]
        arecord_cmd = ["arecord", "-q", "-f", "cd", "-d", str(seconds), wav_out]
        for cmd in (ffmpeg_cmd, arecord_cmd):
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return wav_out
            except FileNotFoundError:
                continue
            except subprocess.CalledProcessError:
                continue
    else:
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-f", "pulse", "-i", "default",
            "-t", str(seconds), "-ac", "1", "-ar", "44100", wav_out,
        ]
        try:
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return wav_out
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

    try:
        os.unlink(wav_out)
    except OSError:
        pass
    raise RuntimeError("Could not capture audio source. Install ffmpeg or arecord.")


def is_youtube_url(url: str) -> bool:
    """Check if a string is a YouTube URL."""
    return "youtube.com" in url or "youtu.be" in url


def download_youtube_audio(url: str) -> str:
    """Download audio from a YouTube URL and return path to WAV file."""
    try:
        import yt_dlp  # type: ignore[import-not-found]
    except ImportError:
        raise RuntimeError(
            "YouTube support requires yt-dlp. Install it with: pip install yt-dlp"
        )

    tmp = tempfile.NamedTemporaryFile(prefix="hacker_youtube_", suffix=".wav", delete=False)
    tmp_wav = tmp.name
    tmp.close()

    tmp_mp3 = tempfile.NamedTemporaryFile(prefix="hacker_youtube_", suffix=".mp3", delete=False)
    tmp_mp3_path = tmp_mp3.name
    tmp_mp3.close()

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": tmp_mp3_path.replace(".mp3", ""),
            "quiet": True,
            "no_warnings": True,
        }

        print(f"Downloading audio from: {url}", file=sys.stderr)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
            ydl.download([url])

        cmd = ["ffmpeg", "-y", "-i", tmp_mp3_path, "-ac", "1", "-ar", "44100", tmp_wav]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except FileNotFoundError as exc:
            raise RuntimeError("ffmpeg required for YouTube audio conversion") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError("ffmpeg failed to convert YouTube audio") from exc

        print(f"YouTube audio saved to: {tmp_wav}", file=sys.stderr)
        return tmp_wav

    finally:
        try:
            os.unlink(tmp_mp3_path)
        except OSError:
            pass


def prepare_audio_input(args: object, audio_path: str) -> Tuple[str, str, bool]:
    """Prepare audio input for processing. Returns (wav_path, playback_path, cleanup_needed)."""
    source = getattr(args, "source", "file")
    keep_converted = getattr(args, "keep_converted", False)
    capture_seconds = getattr(args, "capture_seconds", 30)

    if source == "file":
        if not audio_path:
            raise RuntimeError("Audio file path is required in file mode")

        if is_youtube_url(audio_path):
            try:
                wav_input = download_youtube_audio(audio_path)
                return wav_input, wav_input, True
            except RuntimeError as e:
                print(f"YouTube support unavailable: {e}", file=sys.stderr)
                print("Please provide a local audio file instead.", file=sys.stderr)
                raise

        if not os.path.exists(audio_path):
            raise RuntimeError(f"Audio file not found: {audio_path}")
        wav_input, cleanup = ensure_wav_input(audio_path, keep_converted=keep_converted)
        return wav_input, wav_input, cleanup

    captured = capture_to_wav(source, capture_seconds)
    print(f"Captured {source} audio to: {captured}", file=sys.stderr)
    return captured, captured, True