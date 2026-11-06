"""Timed lyrics for the renderer.

The skull in the center panel only lips-syncs when it has *timed* lines, so
this module is strict: plain (untimed) lyrics are reported but never treated as
syncable. Sources, in order:

1. a sidecar ``.lrc`` next to the audio file (what most players write),
2. lyrics tags embedded in the container (read with ffprobe),
3. ``lrclib.net`` when enabled -- cached on disk, so a track is looked up once.

Everything here is pure except :func:`load_for_track` and the cache, which makes
the parsing testable without a renderer, a terminal or a network.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from cmd_audio.logging_config import get_logger
from cmd_audio.music_meta import _ffprobe_tags, clean_name

logger = get_logger(__name__)

# [mm:ss.xx] / [mm:ss:xx] / [mmm:ss]
_TIME_RE = re.compile(r"\[(\d{1,3}):(\d{1,2})(?:[.:](\d{1,3}))?\]")
_OFFSET_RE = re.compile(r"\[offset:\s*([+-]?\d+)\s*\]", re.IGNORECASE)
_TAG_KEYS = (
    "lyrics", "syncedlyrics", "synced_lyrics", "synclyrics", "unsyncedlyrics",
    "unsynced_lyrics", "lyrics-eng", "lyrics_eng",
)

LRCLIB_URL = "https://lrclib.net/api/get"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "cmd-audio", "lyrics")


@dataclass(frozen=True)
class LyricLine:
    """One timed line."""

    t: float
    text: str


@dataclass
class Lyrics:
    """A parsed lyric set for one track."""

    lines: List[LyricLine] = field(default_factory=list)
    source: str = ""
    timed: bool = False

    def __bool__(self) -> bool:
        return bool(self.lines)

    @property
    def first_t(self) -> float:
        return self.lines[0].t if self.lines else 0.0

    def at(self, t: float) -> Tuple[int, str, str]:
        """Return ``(index, text, next_text)`` for time *t*.

        ``index`` is -1 before the first line. Lines with empty text (musical
        breaks in most LRC files) come back as an empty string so the renderer
        can hide the skull instead of freezing a stale line.
        """
        if not self.lines:
            return -1, "", ""
        if not self.timed:
            # Untimed lyrics cannot say which line is being sung.
            return -1, "", self.lines[0].text
        if t < self.lines[0].t:
            return -1, "", self.lines[0].text

        lo, hi = 0, len(self.lines) - 1
        idx = 0
        while lo <= hi:
            mid = (lo + hi) // 2
            if self.lines[mid].t <= t:
                idx = mid
                lo = mid + 1
            else:
                hi = mid - 1

        text = self.lines[idx].text
        nxt = self.lines[idx + 1].text if idx + 1 < len(self.lines) else ""
        return idx, text, nxt


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _stamp(minutes: str, seconds: str, frac: Optional[str]) -> float:
    value = int(minutes) * 60 + int(seconds)
    if frac:
        value += int(frac) / (10 ** len(frac))
    return float(value)


def parse_lrc(text: str) -> List[LyricLine]:
    """Parse LRC text into sorted, timed lines.

    Handles multiple timestamps on one line, ``[offset:ms]`` and the metadata
    tags (``[ar:]``, ``[ti:]``, ``[by:]``) that carry no time.
    """
    if not text:
        return []

    offset_ms = 0.0
    m = _OFFSET_RE.search(text)
    if m:
        try:
            offset_ms = float(m.group(1))
        except ValueError:
            offset_ms = 0.0

    found: List[LyricLine] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        stamps = _TIME_RE.findall(raw)
        if not stamps:
            continue
        body = _TIME_RE.sub("", raw).strip()
        body = re.sub(r"<\d{1,3}:\d{1,2}(?:[.:]\d{1,3})?>", "", body).strip()
        for parts in stamps:
            t = _stamp(*parts) + offset_ms / 1000.0
            found.append(LyricLine(max(0.0, t), body))

    found.sort(key=lambda line: line.t)

    # Duplicate timestamps are common in karaoke files (one per syllable
    # group); keep the last, it is the completed line.
    deduped: List[LyricLine] = []
    for line in found:
        if deduped and abs(deduped[-1].t - line.t) < 0.01:
            deduped[-1] = line
        else:
            deduped.append(line)
    return deduped


def parse_plain(text: str) -> List[LyricLine]:
    """Untimed lyrics -> one line each, all stamped at 0 (not syncable)."""
    if not text:
        return []
    out: List[LyricLine] = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        body = raw.strip()
        if body:
            out.append(LyricLine(0.0, body))
    return out


def looks_timed(text: str) -> bool:
    return bool(text) and len(_TIME_RE.findall(text)) >= 2


def from_text(text: str, source: str = "") -> Lyrics:
    """Build a :class:`Lyrics` from raw text, detecting whether it is timed."""
    if looks_timed(text):
        return Lyrics(parse_lrc(text), source=source, timed=True)
    return Lyrics(parse_plain(text), source=source, timed=False)


# ---------------------------------------------------------------------------
# Local sources
# ---------------------------------------------------------------------------

def sidecar_path(audio_path: str) -> Optional[str]:
    """Return the ``.lrc`` file that sits next to *audio_path*, if any."""
    if not audio_path or not os.path.isfile(audio_path):
        return None
    stem, _ext = os.path.splitext(audio_path)
    for candidate in (stem + ".lrc", stem + ".LRC", stem + ".Lrc"):
        if os.path.isfile(candidate):
            return candidate
    return None


def _read_text(path: str) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with open(path, "r", encoding=encoding) as fh:
                return fh.read()
        except (OSError, UnicodeDecodeError):
            continue
    return ""


def from_file(path: str, source: str = "") -> Optional[Lyrics]:
    """Parse a lyric file on disk (usually ``.lrc``)."""
    if not path or not os.path.isfile(path):
        return None
    text = _read_text(path)
    if not text.strip():
        return None
    lyrics = from_text(text, source=source or os.path.basename(path))
    return lyrics if lyrics.lines else None


def from_sidecar(audio_path: str) -> Optional[Lyrics]:
    path = sidecar_path(audio_path)
    if not path:
        return None
    return from_file(path)


def from_tags(audio_path: str) -> Optional[Lyrics]:
    """Embedded lyrics tag (timed or not)."""
    if not audio_path or not os.path.isfile(audio_path):
        return None
    tags = _ffprobe_tags(audio_path)
    for key in _TAG_KEYS:
        raw = tags.get(key)
        if not raw or not raw.strip():
            continue
        # ffprobe JSON-escapes newlines in tags.
        raw = raw.replace("\\n", "\n")
        lyrics = from_text(raw, source=f"tag:{key}")
        if lyrics.lines:
            return lyrics
    return None


# ---------------------------------------------------------------------------
# lrclib.net
# ---------------------------------------------------------------------------

def split_artist_title(display_name: str) -> Tuple[str, str]:
    """``"Daft Punk - Get Lucky"`` -> ``("Daft Punk", "Get Lucky")``."""
    name = clean_name(display_name)
    for sep in (" - ", " – ", " — ", " ~ "):
        if sep in name:
            artist, title = name.split(sep, 1)
            if artist.strip() and title.strip():
                return artist.strip(), title.strip()
    return "", name.strip()


def _cache_path(artist: str, title: str, duration: float) -> str:
    key = f"{artist.lower()}|{title.lower()}|{int(duration or 0)}"
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return os.path.join(CACHE_DIR, digest + ".lrc")


def _read_cache(artist: str, title: str, duration: float) -> Optional[str]:
    path = _cache_path(artist, title, duration)
    if os.path.isfile(path):
        text = _read_text(path)
        if text.strip():
            return text
    return None


def _write_cache(artist: str, title: str, duration: float, text: str) -> None:
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(_cache_path(artist, title, duration), "w", encoding="utf-8") as fh:
            fh.write(text)
    except OSError as exc:
        logger.debug("Lyrics cache write failed: %s", exc)


def fetch_online(artist: str, title: str, duration: float = 0.0, timeout: float = 4.0) -> Optional[str]:
    """Fetch synced lyrics from lrclib.net. Returns raw LRC or None."""
    if not title:
        return None

    cached = _read_cache(artist, title, duration)
    if cached:
        return cached

    params = {"track_name": title}
    if artist:
        params["artist_name"] = artist
    if duration and duration > 5:
        params["duration"] = str(int(round(duration)))
    url = LRCLIB_URL + "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, headers={"User-Agent": "cmd-audio/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", "replace"))
    except Exception as exc:  # network, DNS, JSON, 404 -- all mean "no lyrics"
        logger.debug("lrclib lookup failed for %r: %s", title, exc)
        return None

    text = (payload or {}).get("syncedLyrics") or ""
    if not text.strip():
        return None
    _write_cache(artist, title, duration, text)
    return text


def load_for_track(
    audio_path: str,
    display_name: str = "",
    duration: float = 0.0,
    online: bool = True,
) -> Lyrics:
    """Best available lyrics for a track. Empty (falsy) when there are none.

    Only ``timed`` lyrics drive the skull; untimed ones are returned so callers
    can tell the difference between "no lyrics" and "lyrics without timings".
    """
    fallback: Optional[Lyrics] = None
    for loader in (from_sidecar, from_tags):
        try:
            found = loader(audio_path)  # type: ignore[operator]
        except Exception as exc:
            logger.debug("lyrics loader %s failed: %s", getattr(loader, "__name__", loader), exc)
            found = None
        if not found or not found.lines:
            continue
        if found.timed:
            return found
        # Untimed lyrics still beat nothing, but keep looking for a timed set.
        fallback = fallback or found

    if online:
        artist, title = split_artist_title(display_name or audio_path)
        raw = fetch_online(artist, title, duration)
        if raw:
            lyrics = from_text(raw, source="lrclib")
            if lyrics.lines:
                return lyrics

    return fallback or Lyrics(source="none")


def load_async(*args, **kwargs) -> "LyricsLoader":
    """Start :func:`load_for_track` in a thread (a lookup must not stall a frame)."""
    loader = LyricsLoader(args, kwargs)
    loader.start()
    return loader


class LyricsLoader:
    """Thread wrapper so a slow lookup never blocks the render loop."""

    def __init__(self, args: Sequence, kwargs: dict) -> None:
        self._result: Lyrics = Lyrics()
        self._done = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(args, kwargs), daemon=True)

    def _run(self, args: Sequence, kwargs: dict) -> None:
        try:
            self._result = load_for_track(*args, **kwargs)  # type: ignore[arg-type]
        except Exception as exc:
            logger.debug("lyrics load failed: %s", exc)
            self._result = Lyrics()
        finally:
            self._done.set()

    def start(self) -> "LyricsLoader":
        self._thread.start()
        return self

    @property
    def done(self) -> bool:
        return self._done.is_set()

    def result(self) -> Lyrics:
        """The lyrics if the lookup finished, otherwise empty."""
        return self._result if self._done.is_set() else Lyrics()

    def wait(self, timeout: Optional[float] = None) -> Lyrics:
        self._done.wait(timeout)
        return self._result
