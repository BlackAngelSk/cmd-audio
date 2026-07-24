"""Tests for configuration constants and helpers."""

from __future__ import annotations

import pytest

from cmd_audio.config import (
    THEMES,
    THEME_MODES,
    PRESETS,
    SCENE_PACKS,
    TERMINAL_PROFILES,
    MISSION_PHASES,
    OPERATION_MODES,
    TARGETS,
    FREQ_CENTERS,
    apply_theme,
    set_bar_mode,
    set_theme_mode,
    set_bass_threshold,
    CURRENT_THEME_MODE,
    BASS_THRESHOLD,
)


class TestThemes:
    def test_themes_exist(self) -> None:
        assert len(THEMES) > 0

    def test_themes_have_colors(self) -> None:
        for name, theme in THEMES.items():
            assert isinstance(theme, tuple)
            assert len(theme) == 3

    def test_theme_modes(self) -> None:
        assert "manual" in THEME_MODES
        assert "bass" in THEME_MODES


class TestPresets:
    def test_presets_exist(self) -> None:
        assert len(PRESETS) > 0

    def test_presets_are_dicts(self) -> None:
        for name, preset in PRESETS.items():
            assert isinstance(preset, dict)


class TestScenePacks:
    def test_scene_packs_exist(self) -> None:
        assert len(SCENE_PACKS) > 0

    def test_scene_packs_have_weights(self) -> None:
        for name, pack in SCENE_PACKS.items():
            assert isinstance(pack, dict)


class TestTerminalProfiles:
    def test_profiles_exist(self) -> None:
        assert len(TERMINAL_PROFILES) > 0


class TestMissionPhases:
    def test_phases_exist(self) -> None:
        assert len(MISSION_PHASES) > 0

    def test_phases_have_required_keys(self) -> None:
        for phase in MISSION_PHASES:
            assert "name" in phase
            assert "objective" in phase
            assert "operation" in phase
            assert "clearance" in phase
            assert "net_state" in phase


class TestOperationModes:
    def test_modes_exist(self) -> None:
        assert len(OPERATION_MODES) > 0


class TestTargets:
    def test_targets_exist(self) -> None:
        assert len(TARGETS) > 0


class TestFreqCenters:
    def test_freq_centers(self) -> None:
        assert len(FREQ_CENTERS) > 0
        for f in FREQ_CENTERS:
            assert f > 0


class TestApplyTheme:
    def test_valid_theme(self) -> None:
        result = apply_theme("matrix")
        assert isinstance(result, str)

    def test_invalid_theme(self) -> None:
        result = apply_theme("nonexistent_theme")
        assert isinstance(result, str)  # Should return default


class TestSetBarMode:
    def test_set_bar_mode(self) -> None:
        set_bar_mode(True)
        set_bar_mode(False)


class TestSetThemeMode:
    def test_set_theme_mode(self) -> None:
        set_theme_mode("manual")
        set_theme_mode("bass")


class TestSetBassThreshold:
    def test_set_bass_threshold(self) -> None:
        set_bass_threshold(0.5)
        set_bass_threshold(0.1)