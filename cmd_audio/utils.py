"""General-purpose utility functions used across the package."""

from __future__ import annotations

import math
import re
import unicodedata
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Numeric helpers
# ---------------------------------------------------------------------------

def clamp(v: float, lo: float, hi: float) -> float:
    """Clamp *v* between *lo* and *hi*."""
    return max(lo, min(hi, v))


def smooth(vals: List[float], radius: int = 2) -> List[float]:
    """Simple moving-average smoothing."""
    out: List[float] = []
    for i in range(len(vals)):
        a = max(0, i - radius)
        b = min(len(vals), i + radius + 1)
        s = vals[a:b]
        out.append(sum(s) / len(s))
    return out


def normalize(vals: List[float]) -> List[float]:
    """Normalise a list to [0, 1] with a square-root mapping."""
    if not vals:
        return []
    lo = min(vals)
    hi = max(vals)
    span = hi - lo
    if span <= 1e-9:
        return [0.0 for _ in vals]
    return [math.sqrt(max(0.0, (v - lo) / span)) for v in vals]


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
_ESC = "\x1b"

# Terminators that end a colour state. Used when we have to clip coloured text
# so the colour does not bleed into the rest of the line.
_RESET = "\x1b[0m"


_WIDE_EAW = ("W", "F")


def char_width(ch: str) -> int:
    """Display width of a single character (2 for East-Asian wide glyphs)."""
    return 2 if unicodedata.east_asian_width(ch) in _WIDE_EAW else 1


def display_width(text: str) -> int:
    """Display width of *text* in terminal columns (assumes no ANSI escapes)."""
    if text.isascii():
        return len(text)
    return sum(char_width(ch) for ch in text)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from *text*."""
    if _ESC not in text:
        return text
    return _ANSI_RE.sub("", text)


def visible_len(text: str) -> int:
    """Return the visible width of *text* in columns (ignoring ANSI escapes).

    Wide (CJK) glyphs count as two columns, matching what the terminal draws --
    otherwise a single ``堡垒`` in a hostname silently shifts a whole panel.
    """
    if _ESC not in text:
        return len(text) if text.isascii() else display_width(text)
    plain = _ANSI_RE.sub("", text)
    return len(plain) if plain.isascii() else display_width(plain)


def _advance(text: str, i: int, budget: int) -> Tuple[int, int]:
    """Consume characters from *text* at *i* until *budget* columns are used.

    Returns ``(new_index, columns_used)``. ANSI escapes are consumed for free.
    """
    n = len(text)
    used = 0
    while i < n and used < budget:
        if text[i] == _ESC:
            m = _ANSI_RE.match(text, i)
            if m:
                i = m.end()
                continue
        w = 1 if text[i].isascii() else char_width(text[i])
        if used + w > budget:
            break
        used += w
        i += 1
    return i, used


def crop_visible(text: str, width: int) -> str:
    """Crop *text* to at most *width* visible columns (ANSI aware, no padding).

    Unlike :func:`fit_text` this never pads and never appends ``~``; it is the
    primitive used for horizontal shifting where exact column counts matter.
    """
    if width <= 0:
        return ""
    if _ESC not in text:
        return text[:width] if text.isascii() else text[: _advance(text, 0, width)[0]]

    i, _used = _advance(text, 0, width)
    cropped = text[:i]
    if i < len(text):
        cropped += _RESET
    return cropped


def fit_text(text: str, width: int) -> str:
    """Fit *text* to *width* columns, clipping with '~' if needed."""
    if width <= 0:
        return ""

    if text.isascii():
        if _ESC not in text:
            n = len(text)
            if n == width:
                return text
            if n < width:
                return text + (" " * (width - n))
            if width == 1:
                return "~"
            return text[: width - 1] + "~"

        vis = len(_ANSI_RE.sub("", text))
        if vis == width:
            return text
        if vis < width:
            return text + (" " * (width - vis))
        if width == 1:
            return "~"

        i, _used = _advance(text, 0, width - 1)
        return text[:i] + "~" + _RESET

    vis = visible_len(text)
    if vis == width:
        return text
    if vis < width:
        return text + (" " * (width - vis))
    if width == 1:
        return "~"

    i, _used = _advance(text, 0, width - 1)
    clipped = text[:i] + "~"
    if _ESC in text:
        # Re-close any colour state that was cut off mid-line.
        clipped += _RESET
    return clipped


def center_text(text: str, width: int) -> str:
    """Centre *text* within *width* columns."""
    if width <= 0:
        return ""
    vis = visible_len(text)
    if vis >= width:
        return fit_text(text, width)
    left = max(0, (width - vis) // 2)
    right = width - vis - left
    return (" " * left) + text + (" " * right)


def align_text(text: str, width: int, align: str) -> str:
    """Align *text* (left / centre / right) within *width*."""
    clipped = fit_text(text, width)
    if align == "left":
        return clipped
    if align == "right":
        vis = visible_len(text)
        if vis >= width:
            return clipped
        pad = " " * max(0, width - vis)
        return pad + text
    return center_text(text, width)


# ---------------------------------------------------------------------------
# Semantic colour helpers
# ---------------------------------------------------------------------------

def semantic_color(risk: float) -> str:
    """Return an ANSI colour code depending on risk level."""
    from cmd_audio.config import STATUS_CRIT, STATUS_OK, STATUS_WARN

    if risk >= 0.75:
        return STATUS_CRIT
    if risk >= 0.45:
        return STATUS_WARN
    return STATUS_OK


def colorize_status(text: str, risk: float) -> str:
    """Wrap *text* with a risk-dependent ANSI colour."""
    from cmd_audio.config import RESET

    return f"{semantic_color(risk)}{text}{RESET}"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def random_ipv4() -> str:
    """Generate a random IPv4 address string."""
    import random
    return ".".join(str(random.randint(10, 250)) for _ in range(4))

