"""Tests for mission timeline progression and defender AI."""

from __future__ import annotations

import pytest

from cmd_audio.mission import (
    IncidentFeedState,
    MissionTimeline,
    maybe_apply_defender_countermeasure,
    mission_timeline_from_progress,
    should_shift_scene,
)


class TestMissionTimelineFromProgress:
    def test_zero_progress(self) -> None:
        mt = mission_timeline_from_progress(0.0)
        assert mt.phase_idx == 0
        assert isinstance(mt.phase_name, str)
        assert isinstance(mt.objective, str)

    def test_full_progress(self) -> None:
        mt = mission_timeline_from_progress(1.0)
        assert mt.phase_idx >= 0
        assert isinstance(mt.phase_name, str)

    def test_mid_progress(self) -> None:
        mt = mission_timeline_from_progress(0.5)
        assert mt.phase_idx >= 0
        assert isinstance(mt.operation, str)

    def test_clamp_negative(self) -> None:
        mt = mission_timeline_from_progress(-1.0)
        assert mt.phase_idx == 0

    def test_clamp_over_one(self) -> None:
        mt = mission_timeline_from_progress(2.0)
        assert mt.phase_idx >= 0


class TestMaybeApplyDefenderCountermeasure:
    def test_silence(self) -> None:
        result = maybe_apply_defender_countermeasure(
            0.0, False, 0.0, "test-target", "mainframe", 0.1
        )
        assert len(result) == 5
        target, reroute, state, action, events = result
        assert isinstance(target, str)
        assert isinstance(reroute, int)

    def test_high_level(self) -> None:
        result = maybe_apply_defender_countermeasure(
            1.0, True, 1.0, "test-target", "mainframe", 5.0
        )
        assert len(result) == 5


class TestShouldShiftScene:
    def test_adaptive_beat(self) -> None:
        result = should_shift_scene("adaptive", True, 0.8, 5.0, 3.0, False)
        assert isinstance(result, bool)

    def test_bpm(self) -> None:
        result = should_shift_scene("bpm", False, 0.0, 5.0, 3.0, True)
        assert isinstance(result, bool)

    def test_hybrid(self) -> None:
        result = should_shift_scene("hybrid", True, 0.5, 5.0, 3.0, True)
        assert isinstance(result, bool)


class TestIncidentFeedState:
    def test_create(self) -> None:
        state = IncidentFeedState(host="test", phase=0, ttl=10)
        assert state.host == "test"
        assert state.phase == 0
        assert state.ttl == 10