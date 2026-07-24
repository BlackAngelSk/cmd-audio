"""Tests for visual module rendering functions."""

from __future__ import annotations

import pytest

from cmd_audio.visual import (
    VisualState,
    ALL_VISUAL_MODULES,
    build_telemetry_lines,
    generate_shell_feed,
    get_visual_modules_for_cycle,
    refresh_visual_state,
)


class TestVisualState:
    def test_create(self) -> None:
        state = VisualState(
            node_rows=[], file_rows=[],
            firewall_state="OFFLINE", crypto_algo="RSA-2048",
            port_rows=[], admin_rows=[], last_refresh=0.0,
        )
        assert state.firewall_state == "OFFLINE"
        assert state.crypto_algo == "RSA-2048"

    def test_new_module_state_defaults(self) -> None:
        state = VisualState(
            node_rows=[], file_rows=[],
            firewall_state="ONLINE", crypto_algo="AES-256",
            port_rows=[], admin_rows=[], last_refresh=0.0,
        )
        assert state.buffer_overflow_stack == []
        assert state.geo_trace_hops == []
        assert state.vhs_lines == []


class TestAllVisualModules:
    def test_modules_exist(self) -> None:
        assert len(ALL_VISUAL_MODULES) > 0

    def test_modules_are_strings(self) -> None:
        for mod in ALL_VISUAL_MODULES:
            assert isinstance(mod, str)


class TestGenerateShellFeed:
    def test_silence(self) -> None:
        lines = generate_shell_feed(0.0, False, "mainframe")
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_beat(self) -> None:
        lines = generate_shell_feed(0.5, True, "router")
        assert isinstance(lines, list)

    def test_empty(self) -> None:
        lines = generate_shell_feed(1.0, True, "")
        assert isinstance(lines, list)


class TestGetVisualModulesForCycle:
    def test_returns_list(self) -> None:
        result = get_visual_modules_for_cycle(0)
        assert isinstance(result, list)
        assert len(result) > 0


class TestBuildTelemetryLines:
    def test_build(self) -> None:
        lines = build_telemetry_lines(
            level=0.5, t=1.0, duration=10.0, width=40, pulse=0,
            speed_factor=1.0, sensitivity=1.0, theme_name="matrix",
            terminal_mode="mainframe", switch_min=4.0, switch_max=11.0,
            daemon="sshd", clearance="L1", open_ports=5, trace_hops=7,
            packet=5000, flux=0.3, mission_phase="Phase 1",
            mission_objective="Penetrate", defender_state="stable",
            keys_line="keys: q p"
        )
        assert isinstance(lines, list)
        assert len(lines) > 0


class TestRefreshVisualState:
    def test_refresh(self) -> None:
        state = VisualState(
            node_rows=[], file_rows=[],
            firewall_state="OFFLINE", crypto_algo="RSA-2048",
            port_rows=[], admin_rows=[], last_refresh=0.0,
        )
        module_levels = {"buffer-overflow": 0.5, "nodes": 0.3}
        refresh_visual_state(state, module_levels, False, 0.5, 0.0)
        assert isinstance(state.node_rows, list)