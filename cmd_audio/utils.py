"""General-purpose utility functions used across the package."""

from __future__ import annotations

import re
from typing import List


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


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from *text*."""
    return _ANSI_RE.sub("", text)


def visible_len(text: str) -> int:
    """Return the visible length of *text* (ignoring ANSI escapes)."""
    return len(_ANSI_RE.sub("", text))


def fit_text(text: str, width: int) -> str:
    """Fit *text* to *width* columns, clipping with '~' if needed."""
    if width <= 0:
        return ""
    if visible_len(text) <= width:
        return text + (" " * (width - visible_len(text)))
    if width == 1:
        return "~"

    target = width - 1
    out = ""
    vis = 0
    i = 0
    while i < len(text) and vis < target:
        if text[i] == "\x1b":
            m = _ANSI_RE.match(text, i)
            if m:
                out += m.group(0)
                i = m.end()
                continue
        out += text[i]
        vis += 1
        i += 1
    return out + "~"


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


# math is needed by normalize()
import math  # noqa: E402  (placed at end to avoid circular confusion)