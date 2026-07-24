"""Tests for utility functions."""

from __future__ import annotations

import pytest

from cmd_audio.utils import (
    clamp,
    smooth,
    normalize,
    strip_ansi,
    visible_len,
    fit_text,
    center_text,
    align_text,
    semantic_color,
    colorize_status,
    random_ipv4,
)


# ---------------------------------------------------------------------------
# Numeric helpers
# ---------------------------------------------------------------------------

class TestClamp:
    def test_within_range(self) -> None:
        assert clamp(0.5, 0.0, 1.0) == 0.5

    def test_below_range(self) -> None:
        assert clamp(-1.0, 0.0, 1.0) == 0.0

    def test_above_range(self) -> None:
        assert clamp(2.0, 0.0, 1.0) == 1.0

    def test_at_boundary(self) -> None:
        assert clamp(0.0, 0.0, 1.0) == 0.0
        assert clamp(1.0, 0.0, 1.0) == 1.0

    def test_negative_range(self) -> None:
        assert clamp(-5, -10, -1) == -5
        assert clamp(-15, -10, -1) == -10


class TestSmooth:
    def test_empty(self) -> None:
        assert smooth([]) == []

    def test_single(self) -> None:
        assert smooth([1.0]) == [1.0]

    def test_constant(self) -> None:
        result = smooth([1.0, 1.0, 1.0, 1.0, 1.0], radius=1)
        assert all(abs(v - 1.0) < 1e-9 for v in result)

    def test_step(self) -> None:
        result = smooth([0.0, 0.0, 1.0, 1.0, 1.0], radius=1)
        assert len(result) == 5


class TestNormalize:
    def test_empty(self) -> None:
        assert normalize([]) == []

    def test_constant(self) -> None:
        result = normalize([1.0, 1.0, 1.0])
        assert all(v == 0.0 for v in result)

    def test_known(self) -> None:
        result = normalize([0.0, 1.0, 4.0])
        assert len(result) == 3
        for v in result:
            assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

class TestStripAnsi:
    def test_no_ansi(self) -> None:
        assert strip_ansi("hello") == "hello"

    def test_with_ansi(self) -> None:
        text = "\033[92mhello\033[0m"
        assert strip_ansi(text) == "hello"


class TestVisibleLen:
    def test_plain(self) -> None:
        assert visible_len("hello") == 5

    def test_ansi(self) -> None:
        text = "\033[92mhello\033[0m"
        assert visible_len(text) == 5


class TestFitText:
    def test_short(self) -> None:
        result = fit_text("hi", 10)
        assert visible_len(result) == 10

    def test_exact(self) -> None:
        result = fit_text("hello", 5)
        assert visible_len(result) == 5

    def test_long(self) -> None:
        result = fit_text("hello world", 5)
        assert visible_len(result) == 5

    def test_zero_width(self) -> None:
        assert fit_text("hello", 0) == ""


class TestCenterText:
    def test_simple(self) -> None:
        result = center_text("hi", 10)
        assert visible_len(result) == 10
        assert "hi" in result


class TestAlignText:
    def test_left(self) -> None:
        result = align_text("hi", 10, "left")
        assert visible_len(result) == 10

    def test_right(self) -> None:
        result = align_text("hi", 10, "right")
        assert visible_len(result) == 10
        assert result.startswith(" " * 8)

    def test_center(self) -> None:
        result = align_text("hi", 10, "center")
        assert visible_len(result) == 10


# ---------------------------------------------------------------------------
# Semantic color helpers
# ---------------------------------------------------------------------------

class TestSemanticColor:
    def test_low_risk(self) -> None:
        from cmd_audio.config import STATUS_OK
        assert semantic_color(0.0) == STATUS_OK

    def test_medium_risk(self) -> None:
        from cmd_audio.config import STATUS_WARN
        assert semantic_color(0.5) == STATUS_WARN

    def test_high_risk(self) -> None:
        from cmd_audio.config import STATUS_CRIT
        assert semantic_color(0.8) == STATUS_CRIT


class TestColorizeStatus:
    def test_returns_string(self) -> None:
        result = colorize_status("test", 0.0)
        assert isinstance(result, str)
        assert "test" in result


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

class TestRandomIpv4:
    def test_format(self) -> None:
        ip = random_ipv4()
        parts = ip.split(".")
        assert len(parts) == 4
        for part in parts:
            assert part.isdigit()
            assert 0 <= int(part) <= 255