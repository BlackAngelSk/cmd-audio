"""Resolve human-readable track names for audio sources.

The renderer and the control UI must always show a *song name* -- never a raw
YouTube link and never a temporary file path such as
``/tmp/hacker_youtube_ab12cd.wav``.  Everything that displays the current track
goes through :func:`track_display_name`.
"""

from __future__ import annotations

import os
import re
import subprocess
from typing import Dict, Optional

from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)

# Sources that only ever exist as scratch files produced by a download/capture.
_TEMP_PREFIXES = ("hacker_youtube_", "hacker_youtube_cli_", "hacker_sync_", "hacker_mic_", "hacker_system_")

_YOUTUBE_ID_RE = re.compile(r"[\[\(]\s*[A-Za-z0-9_-]{11}\s*[\]\)]")
_BRACKET_NOISE_RE = re.compile(
    r"\s*[\[\(]\s*(official\s*(music\s*)?(video|audio)|lyrics?|audio|hd|hq|4k|"
    r"remaster(ed)?|visualizer|mv)\s*[\]\)]\s*",
    re.IGNORECASE,
)
_WS_RE = re.compile(r"\s{2,}")

# Caches keep ffprobe/yt-dlp out of the render loop.
_name_cache: Dict[str, str] = {}
_youtube_title_cache: Dict[str, str] = {}


def is_temp_source(path: str) -> bool:
    """True for scratch files created by the downloader / capture code."""
    base = os.path.basename(path or "")
    return base.startswith(_TEMP_PREFIXES)


def clean_name(raw: str) -> str:
    """Turn a filename or a messy title into a tidy display name."""
    name = (raw or "").strip()
    if not name:
        return ""
    name = os.path.basename(name)
    root, ext = os.path.splitext(name)
    if ext and len(ext) <= 5:
        name = root
    name = _YOUTUBE_ID_RE.sub(" ", name)
    name = _BRACKET_NOISE_RE.sub(" ", name)
    name = name.replace("_", " ").replace("%20", " ")
    name = _WS_RE.sub(" ", name).strip(" -_.")
    return name


def _ffprobe_tags(path: str, timeout: float = 4.0) -> Dict[str, str]:
    """Read container tags with ffprobe. Returns {} when unavailable."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", path,
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return {}
    if res.returncode != 0 or not res.stdout.strip():
        return {}
    try:
        import json

        data = json.loads(res.stdout)
    except ValueError:
        return {}
    tags = (data.get("format") or {}).get("tags") or {}
    return {str(k).lower(): str(v) for k, v in tags.items()}


def file_track_name(path: str) -> str:
    """Best-effort song name for a local audio file (tags first, filename second)."""
    if not path or not os.path.exists(path):
        return clean_name(path)

    cached = _name_cache.get(path)
    if cached is not None:
        return cached

    title = artist = ""
    tags = _ffprobe_tags(path)
    if tags:
        title = tags.get("title", "").strip()
        artist = tags.get("artist", "").strip() or tags.get("album_artist", "").strip()

    if title:
        name = f"{artist} - {title}" if artist and artist.lower() not in title.lower() else title
        name = clean_name(name) or clean_name(title)
    else:
        name = clean_name(path)

    if not name:
        name = "UNKNOWN TRACK"

    _name_cache[path] = name
    return name


def youtube_title(url: str, fetch: bool = True, timeout: float = 20.0) -> str:
    """Resolve a YouTube URL to its video title (cached). Empty string on failure."""
    if not url:
        return ""
    cached = _youtube_title_cache.get(url)
    if cached:
        return cached
    if not fetch:
        return ""

    # A previously downloaded video may already have published its title.
    try:
        from cmd_audio.audio_input import get_last_youtube_title

        last = get_last_youtube_title()
        if last:
            _youtube_title_cache[url] = last
            return last
    except Exception:
        pass

    cmd = ["yt-dlp", "--no-warnings", "--print", "title", "-q", url]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        logger.debug("yt-dlp title lookup failed: %s", exc)
        return ""
    title = (res.stdout or "").strip().splitlines()
    if res.returncode == 0 and title:
        value = title[-1].strip()
        _youtube_title_cache[url] = value
        return value
    return ""


def remember_youtube_title(url: str, title: str) -> None:
    """Record a title that was discovered while downloading."""
    if url and title:
        _youtube_title_cache[url] = title


def track_display_name(source: str, fallback: str = "DEMO", fetch: bool = True) -> str:
    """Return the name of the song for *source*.

    *source* may be a YouTube URL, a local audio file, an already-known title or
    an internal marker such as ``(demo mode)``. The result is never a URL and
    never a raw path.
    """
    src = (source or "").strip()
    if not src or src.startswith("("):
        return fallback

    if src.startswith("http://") or src.startswith("https://"):
        title = youtube_title(src, fetch=fetch)
        if title:
            return clean_name(title) or title
        # Never render the link itself; fall back to a neutral label.
        return "STREAMING AUDIO"

    if is_temp_source(src):
        # Scratch file: its own name is meaningless to the user.
        try:
            from cmd_audio.audio_input import get_last_youtube_title

            last = get_last_youtube_title()
            if last:
                return clean_name(last) or last
        except Exception:
            pass
        return fallback

    if os.path.exists(src):
        return file_track_name(src)

    return clean_name(src) or fallback
