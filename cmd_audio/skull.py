"""ASCII skull that lips-syncs with the current lyric line.

Three jaw frames of identical geometry, so the skull never shifts when the jaw
moves. The renderer draws the skull plus the line being sung, and ``None`` when
there is nothing timed to show -- the array must look untouched on tracks with
no lyrics.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

# The art is written as-is and padded to a common width at import time, so
# editing one row can never break the alignment of the rest.
_CLOSED: Sequence[str] = (
    r'        ______        ',
    r'     .-"      "-.     ',
    r'    /            \    ',
    r'   |              |   ',
    r'   |,  .-.  .-.  ,|   ',
    r'   | )(_o/  \o_)( |   ',
    r'   |/     /\     \|   ',
    r'   (_     ^^     _)   ',
    r'    \__|IIIIII|__/    ',
    r'     | \IIIIII/ |     ',
    r'      \________/      ',
    r'                      ',
    r'                      ',
)

_HALF: Sequence[str] = (
    r'        ______        ',
    r'     .-"      "-.     ',
    r'    /            \    ',
    r'   |              |   ',
    r'   |,  .-.  .-.  ,|   ',
    r'   | )(_o/  \o_)( |   ',
    r'   |/     /\     \|   ',
    r'   (_     ^^     _)   ',
    r'    \__|IIIIII|__/    ',
    r'     |          |     ',
    r'     |  |IIII|  |     ',
    r'      \________/      ',
    r'                      ',
)

_OPEN: Sequence[str] = (
    r'        ______        ',
    r'     .-"      "-.     ',
    r'    /            \    ',
    r'   |              |   ',
    r'   |,  .-.  .-.  ,|   ',
    r'   | )(_o/  \o_)( |   ',
    r'   |/     /\     \|   ',
    r'   (_     ^^     _)   ',
    r'    \__|IIIIII|__/    ',
    r'     |          |     ',
    r'     |          |     ',
    r'     |  |IIII|  |     ',
    r'      \________/      ',
)

# A five row skull for panels that are too short for the big one.
_SMALL_CLOSED: Sequence[str] = (
    r'   .------.   ',
    r'  / o    o \  ',
    r' |    __    | ',
    r'  \  |__|  /  ',
    r'   `------`   ',
)

_SMALL_OPEN: Sequence[str] = (
    r'   .------.   ',
    r'  / o    o \  ',
    r' |    __    | ',
    r'  \  ||||  /  ',
    r'   `--..--`   ',
)


def _normalise(frames: Sequence[Sequence[str]]) -> List[List[str]]:
    width = max(len(row) for frame in frames for row in frame)
    return [[row.ljust(width) for row in frame] for frame in frames]


_FRAMES = _normalise((_CLOSED, _HALF, _OPEN))
_SMALL_FRAMES = _normalise((_SMALL_CLOSED, _SMALL_CLOSED, _SMALL_OPEN))

SKULL_WIDTH = len(_FRAMES[0][0])
SKULL_HEIGHT = len(_FRAMES[0])
SMALL_WIDTH = len(_SMALL_FRAMES[0][0])
SMALL_HEIGHT = len(_SMALL_FRAMES[0])


def jaw_frame(level: float, beat: bool, fresh: bool) -> int:
    """Pick a jaw frame for the current audio.

    *fresh* means a new lyric line started moments ago -- that opens the jaw
    fully so each line reads as a mouth moving, with the level in between.
    """
    if fresh and level > 0.04:
        return 2
    if beat and level > 0.10:
        return 2
    if level > 0.34:
        return 2
    if level > 0.16:
        return 1
    return 0


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
