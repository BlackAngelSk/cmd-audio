"""ASCII skull that lips-syncs with the current lyric line.

The head stays put and the jaw is a separate piece that drops 0-2 rows, so the
mouth travels instead of the whole skull shifting. Every frame is the same size.

Motion comes from :class:`JawAnimator`: a beat/flux envelope plus a continuous
about-7 Hz "speaking" oscillation. A level threshold alone pins the jaw open on
loud tracks, which is exactly how the skull ends up looking frozen.
"""

from __future__ import annotations

import math
from typing import List, Optional, Sequence

from cmd_audio.utils import clamp

# Rows 0-8 are the head and are shared by every frame; the jaw comes after.
_HEAD: Sequence[str] = (
    r"         .-------.      ",
    r"       .'         '.    ",
    r"      /             \   ",
    r"     |  ( o )  ( o ) |  ",
    r"     |   \_/    \_/  |  ",
    r"     |       /\      |  ",
    r"      \    /    \   /   ",
    r"       '. /      \.'    ",
    r"         \|IIIIIIII|/   ",
)

_CLOSED: Sequence[str] = _HEAD + (
    r"          |IIIIIIII|    ",
    r"           \______/     ",
    r"                        ",
    r"                        ",
)

_HALF: Sequence[str] = _HEAD + (
    r"          |        |    ",
    r"          |IIIIIIII|    ",
    r"           \______/     ",
    r"                        ",
)

_OPEN: Sequence[str] = _HEAD + (
    r"          |        |    ",
    r"          |        |    ",
    r"          |IIIIIIII|    ",
    r"           \______/     ",
)

# A compact skull for panels too short for the big one.
_SMALL_CLOSED: Sequence[str] = (
    r"   .------.   ",
    r"  / o    o \  ",
    r" |    __    | ",
    r"  \  |__|  /  ",
    r"   `------`   ",
)

_SMALL_OPEN: Sequence[str] = (
    r"   .------.   ",
    r"  / o    o \  ",
    r" |    __    | ",
    r"  \  |  |  /  ",
    r"   `--..--`   ",
)


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


_FRAMES = _normalise((_CLOSED, _HALF, _OPEN))
_SMALL_FRAMES = _normalise((_SMALL_CLOSED, _SMALL_CLOSED, _SMALL_OPEN))

SKULL_WIDTH = len(_FRAMES[0][0])
SKULL_HEIGHT = len(_FRAMES[0])
SMALL_WIDTH = len(_SMALL_FRAMES[0][0])
SMALL_HEIGHT = len(_SMALL_FRAMES[0])


class JawAnimator:
    """Continuous jaw opening from level, beats and line changes.

    ``fresh`` fires when a new lyric line starts (full open), ``beat`` adds a
    decaying envelope, and a running oscillator supplies the constant motion
    between beats so a steady loud track still looks like talking.
    """

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
        body.append(f"{accent}{centred}{reset}" if accent else centred)

    body.append(" " * width)

    label = text if len(text) <= width - 2 else text[: max(0, width - 2)] + "~"
    label = label.center(width)
    body.append(f"{bright}{label}{reset}" if bright else label)

    nxt = (next_line or "").strip()
    if nxt:
        label = nxt if len(nxt) <= width - 2 else nxt[: max(0, width - 2)] + "~"
        label = label.center(width)
        body.append(f"{dim}{label}{reset}" if dim else label)

    # keep one clear row between the block and whatever the array draws next
    body.append(" " * width)
    return body


def block_height(small: bool = False) -> int:
    """Rows the block can occupy: art, spacer, line, next line, trail."""
    return (SMALL_HEIGHT if small else SKULL_HEIGHT) + 4
