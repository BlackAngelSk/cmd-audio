"""Live control state (html-based live controls in live_controls.html)."""

from __future__ import annotations

import sys
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from cmd_audio.config import OPERATION_MODES, TARGETS, TERMINAL_PROFILES, THEMES, THEME_MODES
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Runtime snapshot
# ---------------------------------------------------------------------------

@dataclass
class RuntimeSnapshot:
    sensitivity: float
    speed_min: float
    speed_max: float
    terminal_switch_min: float
    terminal_switch_max: float
    theme_name: str
    theme_mode: str
    banner_text: str
    banner_align: str
    banner_anim: str
    banner_size: str
    show_banner: bool
    ui_style: str
    quality_mode: str
    unicode_bars: bool
    scene_sync: str
    terminal_mode: str
    operation_mode: str
    target_lock: str
    lock_scene: bool
    music_file: str
    music_status: str
    frame_drops: int
    alert_tones: bool
    mission_timeline: bool
    defender_ai: bool
    audio_fx: bool
    paused: bool
    quit_requested: bool


# ---------------------------------------------------------------------------
# Thread-safe control state
# ---------------------------------------------------------------------------

class LiveControlState:
    def __init__(
        self,
        sensitivity: float,
        speed_min: float,
        speed_max: float,
        terminal_switch_min: float,
        terminal_switch_max: float,
        theme_name: str,
        theme_mode: str,
        banner_text: str,
        banner_align: str,
        banner_anim: str,
        banner_size: str,
        show_banner: bool,
        ui_style: str,
        quality_mode: str,
        unicode_bars: bool,
        scene_sync: str,
        alert_tones: bool,
        mission_timeline: bool,
        defender_ai: bool,
        audio_fx: bool,
        terminal_mode: str,
        operation_mode: str,
        target_lock: str,
        lock_scene: bool,
        music_file: str,
    ) -> None:
        self._lock = threading.Lock()
        self._sensitivity = sensitivity
        self._speed_min = speed_min
        self._speed_max = speed_max
        self._terminal_switch_min = terminal_switch_min
        self._terminal_switch_max = terminal_switch_max
        self._theme_name = theme_name
        self._theme_mode = theme_mode if theme_mode in THEME_MODES else "manual"
        self._banner_text = banner_text
        self._banner_align = banner_align if banner_align in ("left", "center", "right") else "center"
        self._banner_anim = banner_anim if banner_anim in ("off", "scroll", "pulse") else "off"
        self._banner_size = banner_size if banner_size in ("normal", "large") else "normal"
        self._show_banner = bool(show_banner)
        self._ui_style = ui_style if ui_style in ("full", "minimal") else "full"
        self._quality_mode = quality_mode if quality_mode in ("off", "auto") else "auto"
        self._unicode_bars = bool(unicode_bars)
        self._scene_sync = scene_sync if scene_sync in ("adaptive", "bpm", "hybrid") else "adaptive"
        self._alert_tones = bool(alert_tones)
        self._mission_timeline = bool(mission_timeline)
        self._defender_ai = bool(defender_ai)
        self._audio_fx = bool(audio_fx)
        self._terminal_mode = terminal_mode if terminal_mode in TERMINAL_PROFILES else "netrunner"
        self._operation_mode = operation_mode if operation_mode in OPERATION_MODES else OPERATION_MODES[0]
        self._target_lock = target_lock if target_lock in TARGETS else TARGETS[0]
        self._lock_scene = bool(lock_scene)
        self._music_file = music_file.strip()
        self._music_change_request = ""
        self._music_status = ""
        self._frame_drops = 0
        self._paused = False
        self._quit_requested = False

    def snapshot(self) -> RuntimeSnapshot:
        with self._lock:
            return RuntimeSnapshot(
                sensitivity=self._sensitivity,
                speed_min=self._speed_min,
                speed_max=self._speed_max,
                terminal_switch_min=self._terminal_switch_min,
                terminal_switch_max=self._terminal_switch_max,
                theme_name=self._theme_name,
                theme_mode=self._theme_mode,
                banner_text=self._banner_text,
                banner_align=self._banner_align,
                banner_anim=self._banner_anim,
                banner_size=self._banner_size,
                show_banner=self._show_banner,
                ui_style=self._ui_style,
                quality_mode=self._quality_mode,
                unicode_bars=self._unicode_bars,
                scene_sync=self._scene_sync,
                terminal_mode=self._terminal_mode,
                operation_mode=self._operation_mode,
                target_lock=self._target_lock,
                lock_scene=self._lock_scene,
                music_file=self._music_file,
                music_status=self._music_status,
                frame_drops=self._frame_drops,
                alert_tones=self._alert_tones,
                mission_timeline=self._mission_timeline,
                defender_ai=self._defender_ai,
                audio_fx=self._audio_fx,
                paused=self._paused,
                quit_requested=self._quit_requested,
            )

    def set_sensitivity(self, v: float) -> None:
        from cmd_audio.utils import clamp
        with self._lock:
            self._sensitivity = clamp(v, 0.1, 4.0)

    def set_speed_bounds(self, speed_min: float, speed_max: float) -> None:
        from cmd_audio.utils import clamp
        with self._lock:
            min_v = clamp(speed_min, 0.05, 6.0)
            max_v = clamp(speed_max, min_v, 6.0)
            self._speed_min = min_v
            self._speed_max = max_v

    def set_terminal_switch_bounds(self, switch_min: float, switch_max: float) -> None:
        from cmd_audio.utils import clamp
        with self._lock:
            min_v = clamp(switch_min, 0.5, 60.0)
            max_v = clamp(switch_max, min_v, 60.0)
            self._terminal_switch_min = min_v
            self._terminal_switch_max = max_v

    def set_theme(self, theme_name: str) -> None:
        with self._lock:
            if theme_name in THEMES:
                self._theme_name = theme_name

    def set_theme_mode(self, theme_mode: str) -> None:
        with self._lock:
            if theme_mode in THEME_MODES:
                self._theme_mode = theme_mode

    def set_banner_text(self, banner_text: str) -> None:
        with self._lock:
            self._banner_text = banner_text[:120]

    def set_banner_align(self, banner_align: str) -> None:
        with self._lock:
            if banner_align in ("left", "center", "right"):
                self._banner_align = banner_align

    def set_banner_anim(self, banner_anim: str) -> None:
        with self._lock:
            if banner_anim in ("off", "scroll", "pulse"):
                self._banner_anim = banner_anim

    def set_banner_size(self, banner_size: str) -> None:
        with self._lock:
            if banner_size in ("normal", "large"):
                self._banner_size = banner_size

    def set_show_banner(self, show_banner: bool) -> None:
        with self._lock:
            self._show_banner = bool(show_banner)

    def set_ui_style(self, ui_style: str) -> None:
        with self._lock:
            if ui_style in ("full", "minimal"):
                self._ui_style = ui_style

    def set_quality_mode(self, quality_mode: str) -> None:
        with self._lock:
            if quality_mode in ("off", "auto"):
                self._quality_mode = quality_mode

    def set_unicode_bars(self, enabled: bool) -> None:
        with self._lock:
            self._unicode_bars = bool(enabled)

    def set_scene_sync(self, scene_sync: str) -> None:
        with self._lock:
            if scene_sync in ("adaptive", "bpm", "hybrid"):
                self._scene_sync = scene_sync

    def set_alert_tones(self, enabled: bool) -> None:
        with self._lock:
            self._alert_tones = bool(enabled)

    def set_mission_timeline(self, enabled: bool) -> None:
        with self._lock:
            self._mission_timeline = bool(enabled)

    def set_defender_ai(self, enabled: bool) -> None:
        with self._lock:
            self._defender_ai = bool(enabled)

    def set_audio_fx(self, enabled: bool) -> None:
        with self._lock:
            self._audio_fx = bool(enabled)

    def set_terminal_mode(self, terminal_mode: str) -> None:
        with self._lock:
            if terminal_mode in TERMINAL_PROFILES:
                self._terminal_mode = terminal_mode

    def set_operation_mode(self, operation_mode: str) -> None:
        with self._lock:
            if operation_mode in OPERATION_MODES:
                self._operation_mode = operation_mode

    def set_target_lock(self, target_lock: str) -> None:
        with self._lock:
            cleaned = target_lock.strip()
            if cleaned in TARGETS:
                self._target_lock = cleaned

    def set_lock_scene(self, lock_scene: bool) -> None:
        with self._lock:
            self._lock_scene = bool(lock_scene)

    def set_music_file(self, music_file: str) -> None:
        with self._lock:
            self._music_file = music_file.strip()

    def set_music_status(self, music_status: str) -> None:
        with self._lock:
            self._music_status = music_status[:140]

    def request_music_change(self, music_file: str) -> None:
        with self._lock:
            cleaned = music_file.strip()
            if cleaned:
                self._music_change_request = cleaned

    def consume_music_change(self) -> str:
        with self._lock:
            pending = self._music_change_request
            self._music_change_request = ""
            return pending

    def set_frame_drops(self, frame_drops: int) -> None:
        with self._lock:
            self._frame_drops = max(0, frame_drops)

    def set_paused(self, paused: bool) -> None:
        with self._lock:
            self._paused = paused

    def toggle_paused(self) -> None:
        with self._lock:
            self._paused = not self._paused

    def request_quit(self) -> None:
        with self._lock:
            self._quit_requested = True


# ---------------------------------------------------------------------------
# Live UI handle
# ---------------------------------------------------------------------------

@dataclass
class LiveUIHandle:
    stop_event: threading.Event
    thread: threading.Thread

    def close(self, timeout: float = 1.5) -> None:
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join(timeout=timeout)


