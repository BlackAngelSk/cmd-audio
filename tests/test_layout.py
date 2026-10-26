"""Layout invariants: every rendered row must be exactly as wide as requested.

These guard the regressions that made the frame look broken: rows drifting by a
column (jitter/wide glyphs) and the bottom border being pushed off-screen.
"""

from __future__ import annotations

import random

import pytest

import cmd_audio.config as _cfg
from cmd_audio.effects import apply_terminal_fx, build_banner_lines, panel_box
from cmd_audio.utils import display_width, fit_text, visible_len


def _rows(width: int, height: int) -> list:
    """A frame shaped like the real render loop produces."""
    rows = [
        f"{_cfg.GREEN_DIM}+{'=' * (width - 2)}+{_cfg.RESET}",
        f"{_cfg.GREEN_DIM}|{_cfg.RESET}{fit_text('CMD-AUDIO', width - 2)}{_cfg.GREEN_DIM}|{_cfg.RESET}",
        f"{_cfg.GREEN_DIM}|{_cfg.RESET}{fit_text('Now Playing: Something', width - 2)}{_cfg.GREEN_DIM}|{_cfg.RESET}",
    ]
    body = panel_box("events", width // 2, max(3, height - 5), ["x" * 200] * (height - 5))
    other = panel_box("telemetry", width - width // 2 - 1, max(3, height - 5), ["y"] * (height - 5))
    for i in range(len(body)):
        rows.append(f"{body[i]} {other[i]}")
    rows.append(f"{_cfg.GREEN_DIM}|{_cfg.RESET}{fit_text('::SYNC:: [####] 10%', width - 2)}{_cfg.GREEN_DIM}|{_cfg.RESET}")
    rows.append(f"{_cfg.GREEN_DIM}+{'=' * (width - 2)}+{_cfg.RESET}")
    return rows


@pytest.mark.parametrize("width", [60, 100, 150, 160, 200])
@pytest.mark.parametrize("jitter,glitch,scanline", [(0, 0, 0), (1, 0, 0), (2, 0, 0), (1, 3, 2)])
def test_fx_preserves_row_width(width: int, jitter: int, glitch: int, scanline: int) -> None:
    random.seed(1234)
    rows = _rows(width, 30)
    out = apply_terminal_fx(rows, width, glitch, scanline, jitter, body_start=3)
    for row in out:
        assert visible_len(row) == width, row


def test_jitter_keeps_borders_and_never_adds_tilde() -> None:
    random.seed(7)
    width = 120
    rows = _rows(width, 24)
    before = sum(row.count("~") for row in rows)
    out = apply_terminal_fx(rows, width, 0, 0, 1)
    # jitter must not introduce any new clipping markers...
    assert sum(row.count("~") for row in out) == before
    # ...and the frame borders must survive.
    assert out[0].endswith(f"+{_cfg.RESET}")
    for row in out:
        assert visible_len(row) == width


def test_glitch_tear_keeps_the_frame() -> None:
    random.seed(3)
    width = 120
    rows = _rows(width, 24)
    out = apply_terminal_fx(rows, width, 5, 0, 0, body_start=3)
    torn = [r for r in out if "SIGNAL TEAR" in r]
    assert len(torn) == 1
    assert visible_len(torn[0]) == width
    # the panel frame survives the tear
    assert torn[0].startswith(_cfg.GREEN_DIM)
    assert torn[0].count("|") >= 2


def test_fit_text_always_returns_exact_width() -> None:
    for width in (1, 2, 5, 40):
        assert visible_len(fit_text("", width)) == width
        assert visible_len(fit_text("short", width)) == width
        assert visible_len(fit_text("x" * 300, width)) == width
        assert visible_len(fit_text(f"{_cfg.STATUS_CRIT}coloured text{_cfg.RESET}", width)) == width


def test_banner_lines_are_exactly_one_row_wide() -> None:
    for size in ("normal", "large"):
        for anim in ("off", "scroll", "pulse"):
            random.seed(11)
            lines = build_banner_lines("HELLO WORLD", 150, "center", anim, size, 1.23, 0)
            for line in lines:
                assert display_width(line) == 150, (size, anim, line)


def test_panel_box_rows_are_exact_width() -> None:
    for width, height in ((30, 6), (80, 12), (160, 20)):
        for row in panel_box("t", width, height, ["content"] * height):
            assert visible_len(row) == width
