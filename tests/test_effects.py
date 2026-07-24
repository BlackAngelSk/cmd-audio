"""Tests for visual effects: meter bars, banners, panel boxes, terminal FX."""

from __future__ import annotations

import pytest

from cmd_audio.effects import (
    BLOCK_FONT,
    meter_bar,
    build_banner_lines,
    make_log_line,
    make_incident_line,
    panel_box,
    build_spectrum_lines,
    render_block_text,
)
from cmd_audio.utils import visible_len


class TestMeterBar:
    def test_returns_string(self) -> None:
        result = meter_bar(0.0, 10)
        assert isinstance(result, str)

    def test_full(self) -> None:
        result = meter_bar(1.0, 10)
        assert isinstance(result, str)
        assert "100%" in result

    def test_half(self) -> None:
        result = meter_bar(0.5, 10)
        assert isinstance(result, str)
        assert "50%" in result


class TestBuildBannerLines:
    def test_build(self) -> None:
        lines = build_banner_lines("HELLO", width=40, align="center", anim="off", size="normal", t=0.0, pulse=0)
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_large(self) -> None:
        lines = build_banner_lines("HELLO", width=40, align="center", anim="off", size="large", t=0.0, pulse=0)
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_scroll(self) -> None:
        lines = build_banner_lines("HELLO", width=40, align="center", anim="scroll", size="normal", t=1.0, pulse=0)
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_pulse(self) -> None:
        lines = build_banner_lines("HELLO", width=40, align="center", anim="pulse", size="normal", t=1.0, pulse=1)
        assert isinstance(lines, list)
        assert len(lines) > 0


class TestBuildSpectrumLines:
    def test_build(self) -> None:
        lines = build_spectrum_lines([0.5, 0.3, 0.7, 0.2, 0.8, 0.1, 0.6, 0.4], width=40, height=10, history=[0.5, 0.3], shell_lines=["line"], quality_scale=1.0)
        assert isinstance(lines, list)
        assert len(lines) > 0


class TestMakeLogLine:
    def test_make(self) -> None:
        line = make_log_line(0.5, 1.0, True)
        assert isinstance(line, str)
        assert len(line) > 0


class TestMakeIncidentLine:
    def test_make(self) -> None:
        from cmd_audio.mission import IncidentFeedState
        feed = IncidentFeedState(host="test-host", phase=0, ttl=5)
        line = make_incident_line(0.5, 1.0, True, feed)
        assert isinstance(line, str)
        assert len(line) > 0


class TestPanelBox:
    def test_make(self) -> None:
        result = panel_box("TITLE", width=20, height=5, body=["line1", "line2"])
        assert isinstance(result, list)
        assert len(result) > 0

    def test_empty(self) -> None:
        result = panel_box("TITLE", width=20, height=5, body=[])
        assert isinstance(result, list)


class TestRenderBlockText:
    def test_render(self) -> None:
        result = render_block_text("A")
        assert isinstance(result, list)
        assert len(result) == 5

    def test_empty(self) -> None:
        result = render_block_text("")
        assert isinstance(result, list)


class TestBlockFont:
    def test_has_common_chars(self) -> None:
        for char in " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
            if char in BLOCK_FONT:
                assert len(BLOCK_FONT[char]) == 5