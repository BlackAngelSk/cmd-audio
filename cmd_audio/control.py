"""Live control state and tkinter control window."""

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


def _apply_live_dark_theme(root: Any, style: Any) -> None:
    """Configure a dark cyberpunk colour scheme for the live control window."""
    BG = "#0d1117"
    BG_LIGHT = "#161b22"
    BG_CARD = "#1c2128"
    FG = "#c9d1d9"
    FG_DIM = "#8b949e"
    ACCENT = "#00ff9f"
    BORDER = "#30363d"
    ENTRY_BG = "#0d1117"
    BTN_BG = "#238636"
    BTN_FG = "#ffffff"
    BTN_HOVER = "#2ea043"
    STOP_BG = "#da3633"

    style.theme_use("clam")

    root.configure(bg=BG)

    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=FG, font=("monospace", 10))
    style.configure("Header.TLabel", background=BG, foreground=ACCENT, font=("monospace", 14, "bold"))
    style.configure("SubHeader.TLabel", background=BG, foreground=FG_DIM, font=("monospace", 9))
    style.configure("Field.TLabel", background=BG_CARD, foreground=FG, font=("monospace", 10))
    style.configure("Value.TLabel", background=BG_CARD, foreground=ACCENT, font=("monospace", 9))

    style.configure("TScale",
                     background=BG_CARD, troughcolor=BG,
                     lightcolor=ACCENT, darkcolor=ACCENT,
                     bordercolor=BORDER)
    style.map("TScale",
              background=[("active", BG_CARD)])

    style.configure("TEntry",
                     fieldbackground=ENTRY_BG, foreground=FG,
                     insertcolor=ACCENT, bordercolor=BORDER,
                     lightcolor=BORDER, darkcolor=BORDER,
                     font=("monospace", 10), padding=4)
    style.map("TEntry",
              fieldbackground=[("focus", "#1a2332")],
              foreground=[("disabled", FG_DIM)])

    style.configure("TCombobox",
                     fieldbackground=ENTRY_BG, foreground=FG,
                     background=BG_CARD, arrowcolor=ACCENT,
                     bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                     font=("monospace", 10), padding=4)
    style.map("TCombobox",
              fieldbackground=[("focus", "#1a2332"), ("readonly", ENTRY_BG)],
              foreground=[("readonly", FG)],
              arrowcolor=[("focus", ACCENT)])

    style.configure("TCheckbutton",
                     background=BG, foreground=FG,
                     font=("monospace", 10), padding=2)
    style.map("TCheckbutton",
              background=[("active", BG)],
              foreground=[("active", ACCENT)])

    style.configure("Accent.TButton",
                     background=BTN_BG, foreground=BTN_FG,
                     font=("monospace", 10, "bold"), padding=(12, 6),
                     borderwidth=0)
    style.map("Accent.TButton",
              background=[("active", BTN_HOVER), ("pressed", "#1a7f37")],
              foreground=[("active", BTN_FG)])

    style.configure("Stop.TButton",
                     background=STOP_BG, foreground=BTN_FG,
                     font=("monospace", 10, "bold"), padding=(12, 6),
                     borderwidth=0)
    style.map("Stop.TButton",
              background=[("active", "#f85149")],
              foreground=[("active", BTN_FG)])

    style.configure("Browse.TButton",
                     background=BG_CARD, foreground=ACCENT,
                     font=("monospace", 9), padding=(8, 4),
                     borderwidth=1, relief="solid")
    style.map("Browse.TButton",
              background=[("active", "#1a2332")],
              foreground=[("active", "#ffffff")])

    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab",
                     background=BG_LIGHT, foreground=FG_DIM,
                     font=("monospace", 10, "bold"), padding=(14, 6))
    style.map("TNotebook.Tab",
              background=[("selected", BG_CARD), ("active", "#1a2332")],
              foreground=[("selected", ACCENT), ("active", FG)])

    style.configure("TLabelframe",
                     background=BG_CARD, foreground=ACCENT,
                     bordercolor=BORDER, relief="solid",
                     font=("monospace", 10, "bold"), padding=8)
    style.configure("TLabelframe.Label",
                     background=BG_CARD, foreground=ACCENT,
                     font=("monospace", 10, "bold"))


def start_live_control_window(state: LiveControlState) -> Optional[LiveUIHandle]:
    try:
        import tkinter as tk
        from tkinter import filedialog, ttk
    except Exception:
        logger.warning("UI unavailable: tkinter is not installed")
        return None

    stop_event = threading.Event()

    def ui_thread_main() -> None:
        try:
            root = tk.Tk()
        except Exception as exc:
            logger.error("UI window unavailable: %s", exc)
            return
        root.title("CMD-AUDIO  //  Live Controls")
        root.resizable(True, True)
        root.minsize(720, 580)
        root.configure(bg="#0d1117")

        style = ttk.Style()
        _apply_live_dark_theme(root, style)

        ss = state.snapshot()
        sensitivity_var = tk.DoubleVar(value=ss.sensitivity)
        speed_min_var = tk.DoubleVar(value=ss.speed_min)
        speed_max_var = tk.DoubleVar(value=ss.speed_max)
        switch_min_var = tk.DoubleVar(value=ss.terminal_switch_min)
        switch_max_var = tk.DoubleVar(value=ss.terminal_switch_max)
        theme_var = tk.StringVar(value=ss.theme_name)
        theme_mode_var = tk.StringVar(value=ss.theme_mode)
        banner_var = tk.StringVar(value=ss.banner_text)
        banner_align_var = tk.StringVar(value=ss.banner_align)
        banner_anim_var = tk.StringVar(value=ss.banner_anim)
        banner_size_var = tk.StringVar(value=ss.banner_size)
        show_banner_var = tk.BooleanVar(value=ss.show_banner)
        ui_style_var = tk.StringVar(value=ss.ui_style)
        quality_mode_var = tk.StringVar(value=ss.quality_mode)
        unicode_bars_var = tk.BooleanVar(value=ss.unicode_bars)
        scene_sync_var = tk.StringVar(value=ss.scene_sync)
        alert_tones_var = tk.BooleanVar(value=ss.alert_tones)
        mission_timeline_var = tk.BooleanVar(value=ss.mission_timeline)
        defender_ai_var = tk.BooleanVar(value=ss.defender_ai)
        audio_fx_var = tk.BooleanVar(value=ss.audio_fx)
        terminal_mode_var = tk.StringVar(value=ss.terminal_mode)
        operation_mode_var = tk.StringVar(value=ss.operation_mode)
        target_lock_var = tk.StringVar(value=ss.target_lock)
        lock_scene_var = tk.BooleanVar(value=ss.lock_scene)
        music_choice_var = tk.StringVar(value="")
        music_current_var = tk.StringVar(value=ss.music_file)
        music_status_var = tk.StringVar(value=ss.music_status)
        frame_drops_var = tk.StringVar(value=str(ss.frame_drops))
        paused_var = tk.BooleanVar(value=ss.paused)

        # ── Header ─────────────────────────────────────────────────
        header_frame = ttk.Frame(root)
        header_frame.pack(fill="x", padx=20, pady=(12, 0))
        ttk.Label(header_frame, text="CMD-AUDIO", style="Header.TLabel").pack(anchor="w")
        ttk.Label(header_frame, text="Live control panel — changes apply instantly", style="SubHeader.TLabel").pack(anchor="w", pady=(2, 0))
        sep = tk.Frame(root, height=2, bg="#00ff9f")
        sep.pack(fill="x", padx=20, pady=(6, 0))

        # ── Notebook ───────────────────────────────────────────────
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=20, pady=(10, 0))

        # ── Tab: Playback ──────────────────────────────────────────
        tab_play = ttk.Frame(notebook, padding=12)
        notebook.add(tab_play, text="  Playback  ")
        tab_play.columnconfigure(1, weight=1)

        ttk.Label(tab_play, text="Sensitivity", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Scale(tab_play, from_=0.1, to=4.0, variable=sensitivity_var, orient="horizontal").grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(tab_play, text="Speed Min", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Scale(tab_play, from_=0.05, to=3.0, variable=speed_min_var, orient="horizontal").grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(tab_play, text="Speed Max", style="Field.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Scale(tab_play, from_=0.5, to=6.0, variable=speed_max_var, orient="horizontal").grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(tab_play, text="Switch Min (s)", style="Field.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Scale(tab_play, from_=0.5, to=20.0, variable=switch_min_var, orient="horizontal").grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(tab_play, text="Switch Max (s)", style="Field.TLabel").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Scale(tab_play, from_=1.0, to=60.0, variable=switch_max_var, orient="horizontal").grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Checkbutton(tab_play, text="Pause", variable=paused_var).grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 4))

        ttk.Label(tab_play, text="Frame Drops", style="Field.TLabel").grid(row=6, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Label(tab_play, textvariable=frame_drops_var, style="Value.TLabel").grid(row=6, column=1, sticky="w", pady=4)

        # ── Tab: Visual ────────────────────────────────────────────
        tab_visual = ttk.Frame(notebook, padding=12)
        notebook.add(tab_visual, text="  Visual  ")
        tab_visual.columnconfigure(1, weight=1)

        ttk.Label(tab_visual, text="Theme", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(tab_visual, textvariable=theme_var, values=list(THEMES.keys()), state="readonly").grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(tab_visual, text="Theme Mode", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(tab_visual, textvariable=theme_mode_var, values=["manual", "bass"], state="readonly").grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(tab_visual, text="Scene Sync", style="Field.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(tab_visual, textvariable=scene_sync_var, values=["adaptive", "bpm", "hybrid"], state="readonly").grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(tab_visual, text="UI Style", style="Field.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(tab_visual, textvariable=ui_style_var, values=["full", "minimal"], state="readonly").grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(tab_visual, text="Quality", style="Field.TLabel").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(tab_visual, textvariable=quality_mode_var, values=["auto", "off"], state="readonly").grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Checkbutton(tab_visual, text="Unicode Bars", variable=unicode_bars_var).grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 4))

        # ── Tab: Terminal ──────────────────────────────────────────
        tab_term = ttk.Frame(notebook, padding=12)
        notebook.add(tab_term, text="  Terminal  ")
        tab_term.columnconfigure(1, weight=1)

        ttk.Label(tab_term, text="Terminal Profile", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(tab_term, textvariable=terminal_mode_var, values=list(TERMINAL_PROFILES.keys()), state="readonly").grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(tab_term, text="Operation Mode", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(tab_term, textvariable=operation_mode_var, values=OPERATION_MODES, state="readonly").grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(tab_term, text="Target Lock", style="Field.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(tab_term, textvariable=target_lock_var, values=TARGETS, state="readonly").grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Checkbutton(tab_term, text="Lock Scene", variable=lock_scene_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 4))

        # ── Tab: Banner ────────────────────────────────────────────
        tab_banner = ttk.Frame(notebook, padding=12)
        notebook.add(tab_banner, text="  Banner  ")
        tab_banner.columnconfigure(1, weight=1)

        ttk.Checkbutton(tab_banner, text="Show Banner", variable=show_banner_var).grid(row=0, column=0, columnspan=2, sticky="w", pady=(4, 8))

        ttk.Label(tab_banner, text="Banner Text", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(tab_banner, textvariable=banner_var).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(tab_banner, text="Banner Align", style="Field.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(tab_banner, textvariable=banner_align_var, values=["left", "center", "right"], state="readonly").grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(tab_banner, text="Banner Animation", style="Field.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(tab_banner, textvariable=banner_anim_var, values=["off", "scroll", "pulse"], state="readonly").grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(tab_banner, text="Banner Size", style="Field.TLabel").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(tab_banner, textvariable=banner_size_var, values=["normal", "large"], state="readonly").grid(row=4, column=1, sticky="ew", pady=4)

        # ── Tab: Music ─────────────────────────────────────────────
        tab_music = ttk.Frame(notebook, padding=12)
        notebook.add(tab_music, text="  Music  ")
        tab_music.columnconfigure(1, weight=1)

        ttk.Label(tab_music, text="Current Music", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Label(tab_music, textvariable=music_current_var, style="Value.TLabel").grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(tab_music, text="New Music File", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(tab_music, textvariable=music_choice_var).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(
            tab_music, text="Browse…", style="Browse.TButton",
            command=lambda: music_choice_var.set(filedialog.askopenfilename() or music_choice_var.get()),
        ).grid(row=1, column=2, sticky="w", padx=(8, 0), pady=4)

        def load_music_file() -> None:
            choice = music_choice_var.get().strip()
            if not choice:
                music_status_var.set("Enter a file path first")
                return
            state.set_music_status("Loading requested...")
            state.request_music_change(choice)

        ttk.Button(tab_music, text="Load Music", style="Accent.TButton", command=load_music_file).grid(row=2, column=1, sticky="w", pady=(8, 4))

        # YouTube URL input for live control
        youtube_var = tk.StringVar(value="")
        ttk.Label(tab_music, text="YouTube URL", style="Field.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(tab_music, textvariable=youtube_var).grid(row=3, column=1, sticky="ew", pady=4)

        def load_youtube_music() -> None:
            """Download and load YouTube audio with random attack patterns."""
            url = youtube_var.get().strip()
            if not url:
                music_status_var.set("Enter a YouTube URL first")
                return
            
            if "youtube.com" not in url and "youtu.be" not in url:
                music_status_var.set("Invalid YouTube URL")
                return
            
            music_status_var.set("Downloading YouTube audio...")
            state.request_music_change(url)

        ttk.Button(tab_music, text="Load YouTube", style="Accent.TButton", command=load_youtube_music).grid(row=4, column=1, sticky="w", pady=(8, 4))

        ttk.Label(tab_music, text="Music Status", style="Field.TLabel").grid(row=5, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Label(tab_music, textvariable=music_status_var, style="Value.TLabel").grid(row=5, column=1, sticky="w", pady=4)

        # ── Tab: Features ──────────────────────────────────────────
        tab_feat = ttk.Frame(notebook, padding=12)
        notebook.add(tab_feat, text="  Features  ")
        tab_feat.columnconfigure(0, weight=1)
        tab_feat.columnconfigure(1, weight=1)

        ttk.Checkbutton(tab_feat, text="Alert Tones", variable=alert_tones_var).grid(row=0, column=0, sticky="w", pady=4, padx=4)
        ttk.Checkbutton(tab_feat, text="Mission Timeline", variable=mission_timeline_var).grid(row=0, column=1, sticky="w", pady=4, padx=4)
        ttk.Checkbutton(tab_feat, text="Defender AI", variable=defender_ai_var).grid(row=1, column=0, sticky="w", pady=4, padx=4)
        ttk.Checkbutton(tab_feat, text="Audio FX", variable=audio_fx_var).grid(row=1, column=1, sticky="w", pady=4, padx=4)

        # ── Tab: Streaming & Remote ────────────────────────────────
        tab_stream = ttk.Frame(notebook, padding=12)
        notebook.add(tab_stream, text="  Streaming  ")
        tab_stream.columnconfigure(1, weight=1)

        ttk.Label(tab_stream, text="Streaming Mode", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        stream_mode_var = tk.StringVar(value="file")
        ttk.Combobox(tab_stream, textvariable=stream_mode_var, values=["file", "mic", "system"], state="readonly").grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(tab_stream, text="Sample Rate", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        sample_rate_var = tk.StringVar(value="44100")
        ttk.Combobox(tab_stream, textvariable=sample_rate_var, values=["22050", "44100", "48000"], state="readonly").grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(tab_stream, text="Normalization", style="Field.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        normalize_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab_stream, text="Enable Volume Normalization", variable=normalize_var).grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(tab_stream, text="Web Server", style="Field.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        web_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab_stream, text="Enable Web Server", variable=web_var).grid(row=3, column=1, sticky="w", pady=4)

        web_port_var = tk.IntVar(value=8080)
        ttk.Label(tab_stream, text="Web Port", style="Field.TLabel").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(tab_stream, textvariable=web_port_var, values=["8080", "8081", "8082"], state="readonly").grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(tab_stream, text="Remote Control", style="Field.TLabel").grid(row=5, column=0, sticky="w", padx=(0, 8), pady=4)
        remote_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab_stream, text="Enable Remote Socket", variable=remote_var).grid(row=5, column=1, sticky="w", pady=4)

        remote_port_var = tk.IntVar(value=9999)
        ttk.Label(tab_stream, text="Remote Port", style="Field.TLabel").grid(row=6, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(tab_stream, textvariable=remote_port_var, values=["9998", "9999", "10000"], state="readonly").grid(row=6, column=1, sticky="ew", pady=4)

        # ── Tab: Plugins & Favorites ──────────────────────────────
        tab_plugins = ttk.Frame(notebook, padding=12)
        notebook.add(tab_plugins, text="  Plugins  ")
        tab_plugins.columnconfigure(1, weight=1)

        ttk.Label(tab_plugins, text="Load Plugin", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        plugin_var = tk.StringVar(value="")
        ttk.Entry(tab_plugins, textvariable=plugin_var).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Button(
            tab_plugins, text="Browse…", style="Browse.TButton",
            command=lambda: plugin_var.set(filedialog.askopenfilename(filetypes=[("Python", "*.py")]) or plugin_var.get()),
        ).grid(row=0, column=2, sticky="w", padx=(8, 0), pady=4)

        ttk.Label(tab_plugins, text="Active Plugins", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        plugin_list_var = tk.StringVar(value="(none)")
        ttk.Label(tab_plugins, textvariable=plugin_list_var, style="Value.TLabel").grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(tab_plugins, text="Save Preset", style="Field.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        preset_save_var = tk.StringVar(value="")
        ttk.Entry(tab_plugins, textvariable=preset_save_var).grid(row=2, column=1, sticky="ew", pady=4)

        def save_preset() -> None:
            name = preset_save_var.get().strip()
            if not name:
                return
            from cmd_audio.favorites import save_favorite, FavoritePreset
            snapshot = state.snapshot()
            preset = FavoritePreset(
                name=name,
                theme=snapshot.theme_name,
                sensitivity=snapshot.sensitivity,
                fps=30,
                ui_style=snapshot.ui_style,
                banner_text=snapshot.banner_text,
            )
            save_favorite(preset)
        ttk.Button(tab_plugins, text="Save", style="Accent.TButton", command=save_preset).grid(row=2, column=2, sticky="w", padx=(8, 0), pady=4)

        ttk.Label(tab_plugins, text="Load Preset", style="Field.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        preset_load_var = tk.StringVar(value="")
        ttk.Entry(tab_plugins, textvariable=preset_load_var).grid(row=3, column=1, sticky="ew", pady=4)

        def load_preset() -> None:
            name = preset_load_var.get().strip()
            if not name:
                return
            try:
                from cmd_audio.favorites import load_favorite
                preset = load_favorite(name)
                state.set_theme(preset.theme)
                state.set_sensitivity(preset.sensitivity)
            except Exception:
                pass
        ttk.Button(tab_plugins, text="Load", style="Accent.TButton", command=load_preset).grid(row=3, column=2, sticky="w", padx=(8, 0), pady=4)

        # ── Tab: Scene & Storyboard ────────────────────────────────
        tab_scene = ttk.Frame(notebook, padding=12)
        notebook.add(tab_scene, text="  Scene  ")
        tab_scene.columnconfigure(1, weight=1)

        ttk.Label(tab_scene, text="Scene Pack", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        scene_pack_var = tk.StringVar(value="")
        ttk.Combobox(tab_scene, textvariable=scene_pack_var, values=["default", "hacknet", "cyberpunk", "neon"], state="readonly").grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(tab_scene, text="Storyboard Mode", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        storyboard_var = tk.StringVar(value="off")
        ttk.Combobox(tab_scene, textvariable=storyboard_var, values=["off", "auto", "manual"], state="readonly").grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(tab_scene, text="Layered Rendering", style="Field.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        layered_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab_scene, text="Enable Layered Panels", variable=layered_var).grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(tab_scene, text="Adaptive FPS", style="Field.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        adaptive_fps_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab_scene, text="Enable Adaptive FPS", variable=adaptive_fps_var).grid(row=3, column=1, sticky="w", pady=4)

        # ── Tab: Accessibility ─────────────────────────────────────
        tab_acc = ttk.Frame(notebook, padding=12)
        notebook.add(tab_acc, text="  Access  ")
        tab_acc.columnconfigure(1, weight=1)

        ttk.Label(tab_acc, text="Accessibility Mode", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        acc_var = tk.StringVar(value="off")
        ttk.Combobox(tab_acc, textvariable=acc_var, values=["off", "high-contrast", "screen-reader", "high-contrast+reader"], state="readonly").grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(tab_acc, text="Screen Reader", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        reader_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab_acc, text="Enable Screen Reader Descriptions", variable=reader_var).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(tab_acc, text="Collaborative Mode", style="Field.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        collab_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab_acc, text="Enable Collaborative Session", variable=collab_var).grid(row=2, column=1, sticky="w", pady=4)

        # ── Bottom bar ─────────────────────────────────────────────
        sep2 = tk.Frame(root, height=1, bg="#30363d")
        sep2.pack(fill="x", padx=20, pady=(0, 0))

        def close_only() -> None:
            root.destroy()

        def quit_animation() -> None:
            state.request_quit()
            root.destroy()

        btn_row = ttk.Frame(root)
        btn_row.pack(fill="x", padx=20, pady=(8, 14))
        ttk.Button(btn_row, text="Stop Console", style="Stop.TButton", command=quit_animation).pack(side="right")
        ttk.Button(btn_row, text="Close Window", style="Accent.TButton", command=close_only).pack(side="right", padx=(0, 8))

        # ── Sync logic ─────────────────────────────────────────────
        def sync_to_state(*_: object) -> None:
            state.set_sensitivity(float(sensitivity_var.get()))
            state.set_speed_bounds(float(speed_min_var.get()), float(speed_max_var.get()))
            state.set_terminal_switch_bounds(float(switch_min_var.get()), float(switch_max_var.get()))
            state.set_theme(theme_var.get())
            state.set_theme_mode(theme_mode_var.get())
            state.set_scene_sync(scene_sync_var.get())
            state.set_ui_style(ui_style_var.get())
            state.set_quality_mode(quality_mode_var.get())
            state.set_unicode_bars(bool(unicode_bars_var.get()))
            state.set_alert_tones(bool(alert_tones_var.get()))
            state.set_mission_timeline(bool(mission_timeline_var.get()))
            state.set_defender_ai(bool(defender_ai_var.get()))
            state.set_audio_fx(bool(audio_fx_var.get()))
            state.set_terminal_mode(terminal_mode_var.get())
            state.set_operation_mode(operation_mode_var.get())
            state.set_target_lock(target_lock_var.get())
            state.set_banner_text(banner_var.get())
            state.set_banner_align(banner_align_var.get())
            state.set_banner_anim(banner_anim_var.get())
            state.set_banner_size(banner_size_var.get())
            state.set_show_banner(bool(show_banner_var.get()))
            state.set_lock_scene(bool(lock_scene_var.get()))
            state.set_paused(bool(paused_var.get()))

        for var in (
            sensitivity_var, speed_min_var, speed_max_var,
            switch_min_var, switch_max_var, theme_var, theme_mode_var,
            scene_sync_var, ui_style_var, quality_mode_var,
            unicode_bars_var, alert_tones_var, mission_timeline_var,
            defender_ai_var, audio_fx_var, terminal_mode_var,
            operation_mode_var, target_lock_var, banner_var,
            banner_align_var, banner_anim_var, banner_size_var,
            show_banner_var, lock_scene_var, paused_var,
        ):
            var.trace_add("write", sync_to_state)

        def refresh_from_state() -> None:
            if stop_event.is_set():
                root.destroy()
                return
            ss_now = state.snapshot()
            sensitivity_var.set(ss_now.sensitivity)
            speed_min_var.set(ss_now.speed_min)
            speed_max_var.set(ss_now.speed_max)
            switch_min_var.set(ss_now.terminal_switch_min)
            switch_max_var.set(ss_now.terminal_switch_max)
            theme_var.set(ss_now.theme_name)
            theme_mode_var.set(ss_now.theme_mode)
            scene_sync_var.set(ss_now.scene_sync)
            ui_style_var.set(ss_now.ui_style)
            quality_mode_var.set(ss_now.quality_mode)
            unicode_bars_var.set(ss_now.unicode_bars)
            alert_tones_var.set(ss_now.alert_tones)
            mission_timeline_var.set(ss_now.mission_timeline)
            defender_ai_var.set(ss_now.defender_ai)
            audio_fx_var.set(ss_now.audio_fx)
            terminal_mode_var.set(ss_now.terminal_mode)
            operation_mode_var.set(ss_now.operation_mode)
            target_lock_var.set(ss_now.target_lock)
            music_current_var.set(ss_now.music_file)
            music_status_var.set(ss_now.music_status)
            banner_var.set(ss_now.banner_text)
            banner_align_var.set(ss_now.banner_align)
            banner_anim_var.set(ss_now.banner_anim)
            banner_size_var.set(ss_now.banner_size)
            show_banner_var.set(ss_now.show_banner)
            lock_scene_var.set(ss_now.lock_scene)
            paused_var.set(ss_now.paused)
            frame_drops_var.set(str(ss_now.frame_drops))
            root.after(250, refresh_from_state)

        refresh_from_state()

        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        _tk_vars = (
            sensitivity_var, speed_min_var, speed_max_var,
            switch_min_var, switch_max_var, theme_var,
            banner_var, banner_align_var, banner_anim_var, banner_size_var,
            show_banner_var, ui_style_var, unicode_bars_var,
            alert_tones_var, mission_timeline_var, defender_ai_var, audio_fx_var,
            scene_sync_var, quality_mode_var, terminal_mode_var, operation_mode_var,
            target_lock_var, lock_scene_var, music_choice_var, music_current_var,
            music_status_var, frame_drops_var, paused_var,
        )

        root.mainloop()

        for _var in _tk_vars:
            try:
                _var._tk = None  # type: ignore[attr-defined]
            except Exception:
                pass

    t = threading.Thread(target=ui_thread_main, name="cmd-audio-ui", daemon=False)
    t.start()
    return LiveUIHandle(stop_event=stop_event, thread=t)
