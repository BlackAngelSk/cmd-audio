"""Pixel skull that lips-syncs with the current lyric line.

Rendered with half blocks: each text row covers two sub-rows, so the curves are
smooth instead of stair-stepped, and the rim is drawn brighter than the fill
(``\u2588`` outline, ``\u2593`` interior) so the skull has depth. The head is
fixed and the mandible is a separate piece that drops 0-2 rows.

Blocks need a UTF-8 terminal -- :func:`supports_unicode` is checked once by the
renderer, which skips the skull entirely rather than print mojibake.

Motion comes from :class:`JawAnimator`: a beat envelope plus a continuous
about-7 Hz "speaking" oscillation. A level threshold alone pins the jaw open on
loud tracks, which is exactly how the skull ends up looking frozen.
"""

from __future__ import annotations

import math
import sys
from typing import List, Optional, Sequence

from cmd_audio.utils import clamp

# Head rows are fixed; the rows below are the mandible.
_BIG_HEAD: Sequence[str] = (
    "    ▄██████████████████████████▄",
    "   ▄█▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓█▄",
    "  ▄█▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓█▄",
    "  █▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓█",
    " █▓▓▓▓▓▓▓████▓▓▓▓▓▓▓▓▓▓████▓▓▓▓▓▓▓█",
    " █▓▓▓▓▓█▀    ▀█▓▓▓▓▓▓█▀    ▀█▓▓▓▓▓█",
    " █▓▓▓▓▓█       █▓▓▓▓█       █▓▓▓▓▓█",
    " █▓▓▓▓█         █▓▓█         █▓▓▓▓█",
    " █▓▓▓▓█▄        █▓▓█        ▄█▓▓▓▓█",
    " ▀█▓▓▓▓█       █▓▓▓▓█       █▓▓▓▓█▀",
    "  █▓▓▓▓▓█▄▄  ▄█▓▓▓▓▓▓█▄  ▄▄█▓▓▓▓▓█",
    "   █▓▓▓▓▓▓▓██▓▓▓█▀▀█▓▓▓██▓▓▓▓▓▓▓█",
    "    █▓▓▓▓▓▓▓▓▓▓▓█  █▓▓▓▓▓▓▓▓▓▓▓█",
    "     ▀█▓▓▓▓▓▓▓▓▓█  █▓▓▓▓▓▓▓▓▓█▀",
    "      ▀██▓█▓▓█▓█▄▄▄▄█▓█▓▓█▓██▀",
    "         █ ██ ██ ██ ██ ██ █",
)

_BIG_JAW: Sequence[str] = (
    "        ▀█ ██ ██ ██ ██ ██ █▀",
    "          █▓▓█▓▓█▓▓█▓▓█▓▓█",
    "           █▓▓▓▓▓▓▓▓▓▓▓▓█",
    "            █▓▓▓▓▓▓▓▓▓▓█",
    "             ██████████",
    "",
)

_SMALL_HEAD: Sequence[str] = (
    "  ▄████████████████▄",
    " ▄█▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓█▄",
    " █▓▓▓███▓▓▓▓▓▓███▓▓▓█",
    " █▓▓█   ▀█▓▓█▀   █▓▓█",
    " █▓▓█    ▀██▀    █▓▓█",
    " █▓▓█    █▓▓█    █▓▓█",
    " ▀█▓▓█▄▄█▓▓▓▓█▄▄█▓▓█▀",
    "  ▀█▓▓▓▓▓█▀▀█▓▓▓▓▓█▀",
    "    ▀██▀██ ▄█▀██▀▀",
)

_SMALL_JAW: Sequence[str] = (
    "     ▀█ ██ ██ ██",
    "       █▓▓█▓▓██",
    "        ██████",
)

EDGE = "\u2588"
FILL = "\u2593"


def supports_unicode(stream=None) -> bool:
    """True when the output can carry block glyphs without mojibake."""
    stream = stream if stream is not None else sys.stdout
    encoding = (getattr(stream, "encoding", "") or "").lower().replace("-", "")
    return "utf8" in encoding or "utf_8" in encoding


def _jaw_frames(head: Sequence[str], jaw: Sequence[str]) -> List[List[str]]:
    """Closed / half open / open, with the mandible dropping as one piece."""
    blank = " " * max(len(r) for r in list(head) + list(jaw))
    head = list(head)
    jaw = list(jaw)
    return [head + jaw, head + [blank] + jaw, head + [blank, blank] + jaw]


def _normalise(frames: Sequence[Sequence[str]]) -> List[List[str]]:
    """Pad every frame to one width and height so the art can never jump."""
    width = max(len(row) for frame in frames for row in frame)
    height = max(len(frame) for frame in frames)
    out: List[List[str]] = []
    for frame in frames:
        rows = [row.ljust(width) for row in frame]
        rows += [" " * width] * (height - len(rows))
        out.append(rows)
    return out


_FRAMES = _normalise(_jaw_frames(_BIG_HEAD, _BIG_JAW))
_SMALL_FRAMES = _normalise(_jaw_frames(_SMALL_HEAD, _SMALL_JAW))

SKULL_WIDTH = len(_FRAMES[0][0])
SKULL_HEIGHT = len(_FRAMES[0])
SMALL_WIDTH = len(_SMALL_FRAMES[0][0])
SMALL_HEIGHT = len(_SMALL_FRAMES[0])


class JawAnimator:
    """Continuous jaw opening from level, beats and line changes."""

    def __init__(self, rate: float = 7.0, decay: float = 6.0) -> None:
        self.rate = rate
        self.decay = decay
        self._phase = 0.0
        self._env = 0.0

    def reset(self) -> None:
        self._phase = 0.0
        self._env = 0.0

    def update(self, dt: float, level: float, beat: bool = False, fresh: bool = False) -> float:
        """Advance by *dt* seconds and return the opening in 0..1."""
        dt = clamp(dt, 0.0, 0.25)  # a long stall must not slam the mouth open
        level = clamp(level, 0.0, 1.0)

        if fresh:
            self._env = 1.0
        elif beat:
            self._env = max(self._env, 0.45 + 0.55 * level)
        else:
            self._env = max(0.0, self._env - dt * self.decay)

        self._phase = (self._phase + dt * self.rate * 2.0 * math.pi) % (2.0 * math.pi)
        speech = (0.5 + 0.5 * math.sin(self._phase)) * (0.30 + 0.70 * level)

        return clamp(max(self._env, speech), 0.0, 1.0)


def frame_from_amount(amount: float) -> int:
    """Map a 0..1 jaw opening onto one of the three art frames."""
    if amount < 0.34:
        return 0
    if amount < 0.68:
        return 1
    return 2


def jaw_frame(level: float, beat: bool, fresh: bool) -> int:
    """One-shot mapping for callers that have no frame clock."""
    return frame_from_amount(JawAnimator().update(0.05, level, beat, fresh))


def skull_rows(jaw: int, small: bool = False) -> List[str]:
    """The skull rows for a jaw frame (0 closed .. 2 open)."""
    frames = _SMALL_FRAMES if small else _FRAMES
    return list(frames[max(0, min(2, jaw))])


def _paint(row: str, edge: str, fill: str, reset: str) -> str:
    """Colour the rim brighter than the fill, run by run."""
    out: List[str] = []
    mode = None
    for ch in row:
        if ch == EDGE or ch in "\u2580\u2584":
            want = "edge"
        elif ch == FILL:
            want = "fill"
        else:
            want = None
        if want != mode:
            if mode is not None and reset:
                out.append(reset)
            if want == "edge" and edge:
                out.append(edge)
            elif want == "fill" and fill:
                out.append(fill)
            mode = want
        out.append(ch)
    if mode is not None and reset:
        out.append(reset)
    return "".join(out)


def render_block(
    width: int,
    jaw: int,
    line: str,
    next_line: str,
    bright: str = "",
    dim: str = "",
    accent: str = "",
    reset: str = "",
    small: bool = False,
) -> Optional[List[str]]:
    """Build the overlay block for the current lyric line.

    Returns ``None`` when there is no line to show, which is what keeps the
    array untouched for tracks without timed lyrics -- and also when the panel
    is narrower than the art, because a clipped skull is just noise.
    """
    text = (line or "").strip()
    if not text or width < 4:
        return None

    if not small and width < SKULL_WIDTH:
        small = True
    art = skull_rows(jaw, small=small)
    art_w = max(len(row) for row in art)
    if width < art_w:
        return None

    body: List[str] = []
    for row in art:
        centred = row.ljust(art_w).center(width)
        body.append(_paint(centred, accent, dim, reset) if (accent or dim) else centred)

    body.append(" " * width)

    label = text if len(text) <= width - 2 else text[: max(0, width - 2)] + "~"
    label = label.center(width)
    body.append(bright + label + reset if bright else label)

    nxt = (next_line or "").strip()
    if nxt:
        label = nxt if len(nxt) <= width - 2 else nxt[: max(0, width - 2)] + "~"
        label = label.center(width)
        body.append(dim + label + reset if dim else label)

    # keep one clear row between the block and whatever the array draws next
    body.append(" " * width)
    return body


def block_height(small: bool = False) -> int:
    """Rows the block can occupy: art, spacer, line, next line, trail."""
    return (SMALL_HEIGHT if small else SKULL_HEIGHT) + 4
