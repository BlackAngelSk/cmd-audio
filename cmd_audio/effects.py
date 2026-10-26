"""Visual effects: meter bars, banners, panel boxes, block font, terminal FX."""

from __future__ import annotations

import math
import random
import re
from typing import Dict, List, Optional, Tuple

import cmd_audio.config as _cfg
from cmd_audio.utils import align_text, crop_visible, fit_text, strip_ansi, visible_len


# ---------------------------------------------------------------------------
# Block font for large banner text
# ---------------------------------------------------------------------------

BLOCK_FONT: Dict[str, List[str]] = {
    " ": ["     ", "     ", "     ", "     ", "     "],
    "A": [" ### ", "#   #", "#####", "#   #", "#   #"],
    "B": ["#### ", "#   #", "#### ", "#   #", "#### "],
    "C": [" ####", "#    ", "#    ", "#    ", " ####"],
    "D": ["#### ", "#   #", "#   #", "#   #", "#### "],
    "E": ["#####", "#    ", "#### ", "#    ", "#####"],
    "F": ["#####", "#    ", "#### ", "#    ", "#    "],
    "G": [" ####", "#    ", "# ###", "#   #", " ####"],
    "H": ["#   #", "#   #", "#####", "#   #", "#   #"],
    "I": ["#####", "  #  ", "  #  ", "  #  ", "#####"],
    "J": ["  ###", "   # ", "   # ", "#  # ", " ##  "],
    "K": ["#   #", "#  # ", "###  ", "#  # ", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#####"],
    "M": ["#   #", "## ##", "# # #", "#   #", "#   #"],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", " ### "],
    "P": ["#### ", "#   #", "#### ", "#    ", "#    "],
    "Q": [" ### ", "#   #", "#   #", "#  ##", " ####"],
    "R": ["#### ", "#   #", "#### ", "#  # ", "#   #"],
    "S": [" ####", "#    ", " ### ", "    #", "#### "],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  "],
    "U": ["#   #", "#   #", "#   #", "#   #", " ### "],
    "V": ["#   #", "#   #", "#   #", " # # ", "  #  "],
    "W": ["#   #", "#   #", "# # #", "## ##", "#   #"],
    "X": ["#   #", " # # ", "  #  ", " # # ", "#   #"],
    "Y": ["#   #", " # # ", "  #  ", "  #  ", "  #  "],
    "Z": ["#####", "   # ", "  #  ", " #   ", "#####"],
    "0": [" ### ", "#  ##", "# # #", "##  #", " ### "],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", "#####"],
    "2": [" ### ", "#   #", "  ## ", " #   ", "#####"],
    "3": ["#### ", "    #", " ### ", "    #", "#### "],
    "4": ["#   #", "#   #", "#####", "    #", "    #"],
    "5": ["#####", "#    ", "#### ", "    #", "#### "],
    "6": [" ### ", "#    ", "#### ", "#   #", " ### "],
    "7": ["#####", "    #", "   # ", "  #  ", "  #  "],
    "8": [" ### ", "#   #", " ### ", "#   #", " ### "],
    "9": [" ### ", "#   #", " ####", "    #", " ### "],
    "-": ["     ", "     ", "#####", "     ", "     "],
    "_": ["     ", "     ", "     ", "     ", "#####"],
    ".": ["     ", "     ", "     ", " ##  ", " ##  "],
    "!": ["  #  ", "  #  ", "  #  ", "     ", "  #  "],
    "?": [" ### ", "#   #", "  ## ", "     ", "  #  "],
    ":": ["     ", " ##  ", "     ", " ##  ", "     "],
    "/": ["    #", "   # ", "  #  ", " #   ", "#    "],
    "+": ["     ", "  #  ", "#####", "  #  ", "     "],
    "*": ["# # #", " ### ", "#####", " ### ", "# # #"],
    "@": [" ### ", "#   #", "# ###", "# ###", " ##  "],
    "#": [" # # ", "#####", " # # ", "#####", " # # "],
}


def render_block_text(text: str) -> List[str]:
    """Render text as 5-row ASCII block letters. Each char is 6 columns (5 + 1 gap)."""
    rows = ["", "", "", "", ""]
    unknown = ["  ?  ", "  ?  ", "  ?  ", "     ", "  ?  "]
    for ch in text.upper():
        glyph = BLOCK_FONT.get(ch, unknown)
        for i in range(5):
            rows[i] += glyph[i] + " "
    return rows


# ---------------------------------------------------------------------------
# Meter bar
# ---------------------------------------------------------------------------

def meter_bar(fill_ratio: float, width: int) -> str:
    """Render a progress/meter bar."""
    from cmd_audio.utils import clamp

    ratio = clamp(fill_ratio, 0.0, 1.0)
    bar_w = max(6, width)
    filled = int(round(ratio * bar_w))
    if _cfg.USE_UNICODE_BARS:
        on_ch = "\u2588"
        off_ch = "\u2591"
    else:
        on_ch = _cfg.CURRENT_STYLE["bar_on"]
        off_ch = _cfg.CURRENT_STYLE["bar_off"]
    bar = (on_ch * filled) + (off_ch * (bar_w - filled))
    return f"[{bar}] {int(ratio * 100):3d}%"


# ---------------------------------------------------------------------------
# Panel box
# ---------------------------------------------------------------------------

def panel_box(title: str, width: int, height: int, body: List[str]) -> List[str]:
    """Draw a bordered panel box with a title."""
    width = max(8, width)
    height = max(3, height)
    inner_w = width - 2
    inner_h = height - 2

    label = f"[ {title.upper()} ]"
    if len(label) <= inner_w:
        left = max(0, (inner_w - len(label)) // 2)
        right = max(0, inner_w - len(label) - left)
        top_raw = ("=" * left) + label + ("=" * right)
    else:
        top_raw = "=" * inner_w
    top = f"{_cfg.GREEN_DIM}+{top_raw}+{_cfg.RESET}"
    bottom = f"{_cfg.GREEN_DIM}+{'=' * inner_w}+{_cfg.RESET}"

    lines: List[str] = [top]
    for i in range(inner_h):
        content = fit_text(body[i] if i < len(body) else "", inner_w)
        lines.append(f"{_cfg.GREEN_DIM}|{_cfg.RESET}{content}{_cfg.GREEN_DIM}|{_cfg.RESET}")
    lines.append(bottom)
    return lines


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

def build_banner_line(text: str, width: int, align: str, anim: str, t: float, pulse: int) -> str:
    base = (text.strip() or "CMD-AUDIO ACTIVE")[:240]
    if anim == "scroll":
        padded = f"   {base}   "
        offset = int(t * 8.0) % len(padded)
        track = padded + padded
        return fit_text(track[offset: offset + width], width)
    if anim == "pulse":
        phase = math.sin(t * 5.0)
        marker = "*" if pulse > 0 else ("+" if phase > 0 else ".")
        decorated = f"{marker} {base} {marker}"
        return align_text(decorated, width, align)
    return align_text(base, width, align)


def build_banner_lines(text: str, width: int, align: str, anim: str, size: str, t: float, pulse: int) -> List[str]:
    if size != "large":
        return [build_banner_line(text, width, align, anim, t, pulse)]

    base = (text.strip() or "CMD-AUDIO ACTIVE")[:20]
    block_rows = render_block_text(base)

    if anim == "scroll":
        padded = ["   " + r + "   " for r in block_rows]
        total = len(padded[0])
        # Align offset to character boundaries (each char is 6 columns: 5 + gap)
        # and show whole glyphs only -- a partial glyph at the edge looks broken.
        char_width = 6
        visible = max(1, width // char_width) * char_width
        raw_offset = int(t * 6.0) % max(1, total)
        offset = (raw_offset // char_width) * char_width
        result = []
        for r in padded:
            doubled = r + r + r  # triple to ensure full coverage
            result.append(align_text(doubled[offset: offset + visible], width, "left"))
        return result

    if anim == "pulse":
        phase = math.sin(t * 5.0)
        marker = "*" if pulse > 0 else ("+" if phase > 0 else ".")
        result = []
        for r in block_rows:
            stripped = r.rstrip()
            line = f"{marker} {stripped} {marker}" if stripped.strip() else fit_text("", width)
            result.append(align_text(line, width, align))
        return result

    return [align_text(r, width, align) for r in block_rows]


# ---------------------------------------------------------------------------
# Terminal FX
# ---------------------------------------------------------------------------

_TEAR_MSG = "//// SIGNAL TEAR ////"


def _glitch_row(row: str, width: int, msg: str) -> str:
    """Overlay a glitch message on a framed row without breaking its borders.

    Every box-drawing column of the original row is preserved, so a signal tear
    reads as interference inside the panels instead of a punched-out line.
    """
    plain = strip_ansi(row)
    if len(plain) < 6:
        return fit_text(f"{_cfg.GREEN_BRIGHT}{msg}{_cfg.RESET}", width)

    keep = {i for i, ch in enumerate(plain) if ch in "+|"}
    chars = [ch if i in keep else " " for i, ch in enumerate(plain)]
    msg_cells = set()
    for offset, ch in enumerate(msg):
        pos = 1 + offset
        if pos >= len(chars):
            break
        if pos not in keep:
            chars[pos] = ch
            msg_cells.add(pos)

    parts: List[str] = []
    state = ""
    for i, ch in enumerate(chars):
        want = _cfg.GREEN_DIM if i in keep else (_cfg.GREEN_BRIGHT if i in msg_cells else "")
        if want != state:
            parts.append(want or _cfg.RESET)
            state = want
        parts.append(ch)
    parts.append(_cfg.RESET)
    return "".join(parts)


def _shift_row(row: str, width: int, pad: int) -> str:
    """Shift a row right by *pad* columns without changing its visible width.

    The last visible column is pinned in place, so the box borders survive the
    jitter instead of being cropped off the right edge.
    """
    plain = strip_ansi(row)
    if len(plain) < 3 or plain == " " * len(plain):
        return fit_text(row, width)

    last = plain[-1]
    body = crop_visible(row, len(plain) - 1)
    body = crop_visible(body, max(0, width - pad - 1))
    tail = f"{_cfg.GREEN_DIM}{last}{_cfg.RESET}" if last in "+|" else last
    return fit_text(" " * pad + body, width - 1) + tail


def apply_terminal_fx(
    rows: List[str],
    width: int,
    glitch_frames: int,
    scanline_flash: int,
    jitter: int,
    body_start: int = 3,
) -> List[str]:
    if not rows:
        return rows

    out = list(rows)
    n = len(out)

    if glitch_frames > 0 and n - body_start > 4:
        # Only tear the body area so headers, banner and footer stay readable.
        lo = max(0, body_start)
        hi = max(lo, n - 3)
        tear_line = random.randint(lo, hi)
        out[tear_line] = _glitch_row(out[tear_line], width, _TEAR_MSG)

    if scanline_flash > 0:
        for i in range(max(3, body_start), n - 2, 3):
            out[i] = f"{_cfg.GREEN_DARK}{fit_text(out[i], width)}{_cfg.RESET}"

    if jitter > 0:
        pad = min(2, jitter)
        out = [_shift_row(line, width, pad) for line in out]

    return out


# ---------------------------------------------------------------------------
# Log / incident line generators
# ---------------------------------------------------------------------------

def make_log_line(level: float, t: float, beat: bool) -> str:
    action = random.choice(_cfg.LOG_ACTIONS)
    target = random.choice(_cfg.ALERT_WORDS)
    strength = int(level * 100)
    marker = f"{_cfg.GREEN_BRIGHT}!{_cfg.RESET}" if beat else " "
    host = random.choice(_cfg.TARGETS)
    port = random.choice(_cfg.PORTS)
    pwr = f"{_cfg.GREEN_BRIGHT}{strength:02d}%{_cfg.RESET}" if strength >= 70 else f"{strength:02d}%"
    return f"{marker}{t:06.2f}s {action:<9} {target:<8} {host}:{port} pwr={pwr}"


def make_incident_line(level: float, t: float, beat: bool, feed: "IncidentFeedState") -> str:  # type: ignore[name-defined]
    """Build an incident-feed line, mutating *feed* for stateful progression."""
    stages = [
        "probe accepted",
        "credential replay",
        "privilege pivot",
        "data siphon",
        "trace erasure",
    ]
    if feed.ttl <= 0 or random.random() < 0.1:
        feed.host = random.choice(_cfg.TARGETS)
        feed.phase = 0
        feed.ttl = random.randint(4, 9)
    else:
        feed.phase = min(len(stages) - 1, feed.phase + (1 if random.random() < 0.45 or beat else 0))
        feed.ttl -= 1

    if beat or level > 0.75:
        severity, sev_color = "CRIT", _cfg.STATUS_CRIT
    elif level > 0.45:
        severity, sev_color = "WARN", _cfg.STATUS_WARN
    else:
        severity, sev_color = "INFO", _cfg.GREEN_DIM
    port = random.choice(_cfg.PORTS)
    marker = f"{_cfg.GREEN_BRIGHT}!{_cfg.RESET}" if beat else " "
    stage_text = stages[feed.phase]
    return (
        f"{marker}{t:06.2f}s {_cfg.GREEN_DIM}INCIDENT{_cfg.RESET}  "
        f"{sev_color}{severity:<4}{_cfg.RESET} {feed.host}:{port} {stage_text}"
    )


# ---------------------------------------------------------------------------
# Spectrum lines (used by visual module)
# ---------------------------------------------------------------------------

def build_spectrum_lines(
    bands: List[float],
    width: int,
    height: int,
    history: List[float],
    shell_lines: List[str],
    quality_scale: float,
) -> List[str]:
    bar_w = max(8, int((width - 20) * quality_scale))
    lines: List[str] = []

    band_count = min(len(bands), max(4, int((height - 4) * quality_scale)))
    if _cfg.USE_UNICODE_BARS:
        bar_on = "\u2588"
        bar_off = "\u2591"
    else:
        bar_on = _cfg.CURRENT_STYLE["bar_on"]
        bar_off = _cfg.CURRENT_STYLE["bar_off"]
    spark_lut = _cfg.CURRENT_STYLE["spark"]
    for i in range(band_count):
        from cmd_audio.utils import clamp as _clamp
        b = _clamp(bands[i], 0.0, 1.0)
        filled = int(b * bar_w)
        bar = (bar_on * filled) + (bar_off * (bar_w - filled))
        lines.append(f"B{i + 1:02d} [{bar}] {int(b * 100):3d}%")

    hist_w = max(10, min(width - 10, len(history)))
    hist = history[-hist_w:]
    spark = "".join(spark_lut[min(9, int(v * 9.99))] for v in hist)
    lines.append("")
    lines.append(f"history {spark}")
    room = height - len(lines)
    if room > 0:
        lines.extend(shell_lines[:room])
    return lines[:height]


# ---------------------------------------------------------------------------
# Prompt for banner text (interactive)
# ---------------------------------------------------------------------------

def prompt_banner_text(raw: "RawInput", current_text: str) -> str:  # type: ignore[name-defined]
    """Temporarily leave raw mode to let the user type a custom banner string."""
    import sys

    try:
        raw.disable()
        sys.stdout.write(_cfg.SHOW_CURSOR + _cfg.RESET + "\n")
        sys.stdout.write(f"Banner text (blank keeps current) [{current_text}]: ")
        sys.stdout.flush()
        typed = sys.stdin.readline().rstrip("\n")
        if typed.strip():
            return typed.strip()[:120]
        return current_text
    finally:
        raw.enable()
        sys.stdout.write(_cfg.HIDE_CURSOR)
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# Matrix rain effect
# ---------------------------------------------------------------------------

_RAIN_CHARS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%&*+=<>{}[]|/\\")


def render_matrix_rain(
    width: int,
    height: int,
    level: float,
    columns: Optional[List[Tuple[int, int]]] = None,
    t: float = 0.0,
) -> Tuple[List[str], List[Tuple[int, int]]]:
    """Render a matrix-style falling character rain.

    *columns* is a list of ``(col, head_row)`` pairs tracking each drop.
    On the first call pass ``None`` to auto-initialise.

    Returns ``(lines, updated_columns)`` where *lines* is the rendered frame
    and *updated_columns* should be fed back on the next call.
    """
    from cmd_audio.utils import clamp as _clamp

    activity = _clamp(level, 0.0, 1.0)
    col_count = max(3, int(width * 0.35))
    speed = 1 + int(activity * 3)

    # Initialise columns if needed
    if columns is None:
        columns = [(random.randint(0, width - 1), random.randint(-height, 0)) for _ in range(col_count)]

    # Build a 2-D buffer
    grid: List[List[str]] = [[" "] * width for _ in range(height)]

    alive: List[Tuple[int, int]] = []
    for col, head in columns:
        tail_len = random.randint(3, 8)
        for dy in range(tail_len):
            y = head - dy
            if 0 <= y < height and 0 <= col < width:
                ch = random.choice(_RAIN_CHARS)
                grid[y][col] = ch

        new_head = head + speed
        # Recycle drops that leave the screen
        if new_head - tail_len > height:
            new_head = random.randint(-height // 2, 0)
            col = random.randint(0, width - 1)
        alive.append((col, new_head))

    lines = ["".join(row) for row in grid]
    return lines, alive


# ---------------------------------------------------------------------------
# ASCII waveform display
# ---------------------------------------------------------------------------

_WAVE_CHARS = [" ", ".", "~", "-", "=", "+", "#", "@"]


def render_waveform(
    amplitudes: List[float],
    width: int,
    height: int,
    level: float = 0.0,
) -> List[str]:
    """Render an ASCII waveform from *amplitudes* (values in 0..1).

    The waveform is centred vertically inside a box of *height* rows.
    ``level`` controls the brightness of the centre-line character.
    """
    from cmd_audio.utils import clamp as _clamp

    n = max(1, len(amplitudes))
    mid = height // 2
    lines: List[str] = []
    amp_char_idx = min(len(_WAVE_CHARS) - 1, max(1, int(_clamp(level, 0.0, 1.0) * (len(_WAVE_CHARS) - 1))))

    for row in range(height):
        parts: List[str] = []
        for x in range(width):
            idx = int(x * n / max(1, width)) if width > 0 else 0
            idx = min(idx, n - 1)
            amp = _clamp(amplitudes[idx], 0.0, 1.0)
            peak = int(amp * mid)
            dist = abs(row - mid)
            if dist == 0:
                parts.append(_WAVE_CHARS[amp_char_idx])
            elif dist <= peak:
                parts.append(_WAVE_CHARS[min(len(_WAVE_CHARS) - 1, amp_char_idx + 1)])
            else:
                parts.append(" ")
        lines.append("".join(parts))
    return lines


# ---------------------------------------------------------------------------
# Hex dump view
# ---------------------------------------------------------------------------

_HEX_CHARS = "0123456789ABCDEF"


def render_hex_dump(
    width: int,
    height: int,
    level: float,
    t: float = 0.0,
    base_addr: int = 0x00400000,
) -> List[str]:
    """Render a fake hex-dump panel that reacts to audio level.

    *level* (0..1) controls how many bytes appear highlighted (non-zero).
    *base_addr* is the starting memory address displayed.
    """
    from cmd_audio.utils import clamp as _clamp

    activity = _clamp(level, 0.0, 1.0)
    # Each line: "ADDR  XX XX XX XX  XX XX XX XX  XX XX XX XX  XX XX XX XX  ASCII"
    # e.g.  "00400000  4A 3F 00 8B  FF 12 A0 3C  91 00 00 44  7E 22 FF 01  |J?..<...D.~"..|
    bytes_per_line = 16
    lines: List[str] = []
    seed = int(t * 3)  # changes every ~0.33s

    for row in range(height):
        addr = base_addr + row * bytes_per_line
        addr_str = f"{addr:08X}"

        groups: List[str] = []
        ascii_parts: List[str] = []
        rng = random.Random(addr ^ seed)

        for col in range(bytes_per_line):
            if rng.random() < activity:
                byte_val = rng.randint(0x00, 0xFF)
            else:
                byte_val = rng.randint(0x00, 0x0F)  # mostly zeros / low vals
            hi = _HEX_CHARS[(byte_val >> 4) & 0x0F]
            lo = _HEX_CHARS[byte_val & 0x0F]
            groups.append(f"{hi}{lo}")

            if 0x20 <= byte_val < 0x7F:
                ascii_parts.append(chr(byte_val))
            else:
                ascii_parts.append(".")

        # Insert spacing between 4-byte groups
        formatted_bytes = " ".join(
            " ".join(groups[i : i + 4])
            for i in range(0, len(groups), 4)
        )
        ascii_str = "".join(ascii_parts)
        line = f"{addr_str}  {formatted_bytes}  |{ascii_str}|"

        # Colour-highlight lines with high activity
        if activity > 0.6 and row % 3 == 0:
            line = f"{_cfg.GREEN_DIM}{line}{_cfg.RESET}"

        lines.append(fit_text(line, width))

    return lines[:height]
