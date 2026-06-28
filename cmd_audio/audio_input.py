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


def _download_youtube_via_module(url: str, tmp_mp3_path: str, tmp_wav: str) -> str:
    """Download YouTube audio using the yt_dlp Python module (pip-installed)."""
    import yt_dlp  # type: ignore[import-not-found]

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
        "ignoreerrors": True,
    }

    print(f"Downloading audio from: {url}", file=sys.stderr)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
        try:
            ydl.download([url])
        except Exception as e:
            # If download fails, try to get info and use available format
            try:
                info = ydl.extract_info(url, download=False)
                if info and "formats" in info:
                    # Use the best available format
                    formats = [f for f in (info["formats"] or []) if f.get("url")]
                    if formats:
                        best = formats[0]
                        print(f"Using direct URL: {best.get('url', 'N/A')}", file=sys.stderr)
                        # Download directly using the URL
                        import urllib.request
                        urllib.request.urlretrieve(best["url"], tmp_mp3_path)
                    else:
                        raise RuntimeError(f"No audio formats available for this video: {e}")
                else:
                    raise RuntimeError(f"Could not extract video info: {e}")
            except Exception as inner_e:
                if "YouTube download failed" in str(inner_e):
                    raise inner_e
                raise RuntimeError(f"YouTube download failed: {inner_e}") from e

    # Check if MP3 file was created
    if not os.path.exists(tmp_mp3_path) or os.path.getsize(tmp_mp3_path) == 0:
        raise RuntimeError("YouTube download did not create a valid audio file")

    cmd = ["ffmpeg", "-y", "-i", tmp_mp3_path, "-ac", "1", "-ar", "44100", tmp_wav]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg required for YouTube audio conversion") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("ffmpeg failed to convert YouTube audio") from exc

    print(f"YouTube audio saved to: {tmp_wav}", file=sys.stderr)
    return tmp_wav


def _download_youtube_via_cli(url: str, tmp_wav: str) -> str:
    """Download YouTube audio using the yt-dlp CLI command (system-installed)."""
    # Use a temporary MP3 path for the CLI download
    tmp_mp3 = tempfile.NamedTemporaryFile(prefix="hacker_youtube_cli_", suffix=".mp3", delete=False)
    tmp_mp3_path = tmp_mp3.name
    tmp_mp3.close()

    try:
        print(f"Downloading audio from: {url} (via yt-dlp CLI)", file=sys.stderr)

        # yt-dlp CLI: download best audio, extract as mp3
        yt_cmd = [
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            "--audio-quality", "192K",
            "-o", tmp_mp3_path.replace(".mp3", "%(title)s.%(ext)s"),
            "-q",
            url,
        ]
        try:
            subprocess.run(yt_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except FileNotFoundError:
            raise RuntimeError("yt-dlp CLI not found. Install it via your system package manager or with: pip install yt-dlp")
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"yt-dlp CLI download failed: {exc}") from exc

        # Find the actual downloaded file (yt-dlp may name it differently)
        dl_dir = os.path.dirname(tmp_mp3_path)
        dl_entries = os.listdir(dl_dir) if dl_dir else []
        downloaded_files = [
            f for f in dl_entries
            if f.startswith(os.path.basename(tmp_mp3_path).replace(".mp3", ""))
            and os.path.isfile(os.path.join(dl_dir, f))
        ]
        actual_mp3 = tmp_mp3_path
        if downloaded_files:
            actual_mp3 = os.path.join(os.path.dirname(tmp_mp3_path), downloaded_files[0])

        if not os.path.exists(actual_mp3) or os.path.getsize(actual_mp3) == 0:
            raise RuntimeError("yt-dlp CLI did not produce a valid audio file")

        # Convert to WAV
        cmd = ["ffmpeg", "-y", "-i", actual_mp3, "-ac", "1", "-ar", "44100", tmp_wav]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except FileNotFoundError as exc:
            raise RuntimeError("ffmpeg required for YouTube audio conversion") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError("ffmpeg failed to convert YouTube audio") from exc

        # Clean up the downloaded mp3 if different from tmp_mp3_path
        if actual_mp3 != tmp_mp3_path:
            try:
                os.unlink(actual_mp3)
            except OSError:
                pass

        print(f"YouTube audio saved to: {tmp_wav}", file=sys.stderr)
        return tmp_wav

    finally:
        try:
            os.unlink(tmp_mp3_path)
        except OSError:
            pass


def download_youtube_audio(url: str) -> str:
    """Download audio from a YouTube URL and return path to WAV file.

    Tries two methods in order:
    1. yt_dlp Python module (pip-installed)
    2. yt-dlp CLI command (system-installed via pacman, apt, brew, etc.)
    """
    tmp = tempfile.NamedTemporaryFile(prefix="hacker_youtube_", suffix=".wav", delete=False)
    tmp_wav = tmp.name
    tmp.close()

    # Method 1: try the Python module (pip-installed yt-dlp)
    try:
        import yt_dlp  # type: ignore[import-not-found]
        # If import succeeded, use the module approach
        tmp_mp3 = tempfile.NamedTemporaryFile(prefix="hacker_youtube_", suffix=".mp3", delete=False)
        tmp_mp3_path = tmp_mp3.name
        tmp_mp3.close()
        try:
            return _download_youtube_via_module(url, tmp_mp3_path, tmp_wav)
        finally:
            try:
                os.unlink(tmp_mp3_path)
            except OSError:
                pass
    except ImportError:
        pass

    # Method 2: try the yt-dlp CLI command (system-installed)
    try:
        return _download_youtube_via_cli(url, tmp_wav)
    except RuntimeError:
        # Clean up the WAV file if it was created
        try:
            os.unlink(tmp_wav)
        except OSError:
            pass
        raise RuntimeError(
            "YouTube support requires yt-dlp. Install it with:\n"
            "  - pip install yt-dlp  (Python module)\n"
            "  - Or via your system package manager (apt, pacman, brew, etc.)"
        )


def get_random_attack_pattern() -> dict:
    """Generate random attack pattern for visual effects."""
    import random
    
    attack_types = [
        "matrix_rain",
        "glitch_effect",
        "scanline_flash",
        "color_inversion",
        "pixelation",
        "vhs_tracking",
        "chromatic_aberration",
        "signal_interference",
    ]
    
    patterns = {
        "matrix_rain": {
            "intensity": random.uniform(0.3, 1.0),
            "speed": random.uniform(0.5, 2.0),
            "color_shift": random.choice([True, False]),
        },
        "glitch_effect": {
            "frequency": random.uniform(0.1, 0.8),
            "amplitude": random.uniform(0.2, 1.0),
            "duration": random.uniform(0.1, 0.5),
        },
        "scanline_flash": {
            "width": random.randint(1, 10),
            "speed": random.uniform(1.0, 5.0),
            "opacity": random.uniform(0.3, 1.0),
        },
        "color_inversion": {
            "threshold": random.uniform(0.3, 0.9),
            "fade_speed": random.uniform(0.5, 2.0),
        },
        "pixelation": {
            "block_size": random.randint(2, 16),
            "transition_speed": random.uniform(0.5, 2.0),
        },
        "vhs_tracking": {
            "line_offset": random.randint(1, 20),
            "noise_level": random.uniform(0.1, 0.5),
            "stability": random.uniform(0.3, 0.9),
        },
        "chromatic_aberration": {
            "offset": random.randint(1, 5),
            "direction": random.choice(["horizontal", "vertical", "both"]),
        },
        "signal_interference": {
            "frequency": random.uniform(0.5, 3.0),
            "amplitude": random.uniform(0.2, 0.8),
            "pattern": random.choice(["sine", "square", "sawtooth"]),
        },
    }
    
    selected_attack = random.choice(attack_types)
    return {
        "type": selected_attack,
        "params": patterns[selected_attack],
        "intensity": random.uniform(0.5, 1.0),
        "duration": random.uniform(2.0, 10.0),
    }


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