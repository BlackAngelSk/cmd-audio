"""Pre-run setup popup UI (tkinter) – dark cyberpunk themed."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


def _apply_dark_theme(root, style: Any) -> None:
    """Configure a dark cyberpunk colour scheme for ttk widgets."""
    BG = "#0d1117"
    BG_LIGHT = "#161b22"
    BG_CARD = "#1c2128"
    FG = "#c9d1d9"
    FG_DIM = "#8b949e"
    ACCENT = "#00ff9f"
    ACCENT_DIM = "#00cc7f"
    BORDER = "#30363d"
    ENTRY_BG = "#0d1117"
    BTN_BG = "#238636"
    BTN_FG = "#ffffff"
    BTN_HOVER = "#2ea043"
    CANCEL_BG = "#da3633"
    CANCEL_FG = "#ffffff"

    style.theme_use("clam")

    # Root
    root.configure(bg=BG)

    # Frame
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=BG_CARD)
    style.configure("Tab.TFrame", background=BG)

    # Label
    style.configure("TLabel", background=BG, foreground=FG, font=("monospace", 10))
    style.configure("Header.TLabel", background=BG, foreground=ACCENT, font=("monospace", 16, "bold"))
    style.configure("SubHeader.TLabel", background=BG, foreground=FG_DIM, font=("monospace", 9))
    style.configure("Section.TLabel", background=BG_CARD, foreground=ACCENT, font=("monospace", 11, "bold"))
    style.configure("Field.TLabel", background=BG_CARD, foreground=FG, font=("monospace", 10))
    style.configure("Check.TCheckbutton", background=BG_CARD, foreground=FG, font=("monospace", 10))

    # Entry
    style.configure("TEntry",
                     fieldbackground=ENTRY_BG, foreground=FG,
                     insertcolor=ACCENT, bordercolor=BORDER,
                     lightcolor=BORDER, darkcolor=BORDER,
                     font=("monospace", 10), padding=4)
    style.map("TEntry",
              fieldbackground=[("focus", "#1a2332"), ("disabled", "#0d1117")],
              foreground=[("disabled", FG_DIM)])

    # Combobox
    style.configure("TCombobox",
                     fieldbackground=ENTRY_BG, foreground=FG,
                     background=BG_CARD, arrowcolor=ACCENT,
                     bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                     font=("monospace", 10), padding=4)
    style.map("TCombobox",
              fieldbackground=[("focus", "#1a2332"), ("readonly", ENTRY_BG)],
              foreground=[("readonly", FG)],
              arrowcolor=[("focus", ACCENT)])

    # Checkbutton
    style.configure("TCheckbutton",
                     background=BG_CARD, foreground=FG,
                     font=("monospace", 10), padding=2)
    style.map("TCheckbutton",
              background=[("active", BG_CARD)],
              foreground=[("active", ACCENT)])

    # Button
    style.configure("Accent.TButton",
                     background=BTN_BG, foreground=BTN_FG,
                     font=("monospace", 11, "bold"), padding=(16, 8),
                     borderwidth=0)
    style.map("Accent.TButton",
              background=[("active", BTN_HOVER), ("pressed", "#1a7f37")],
              foreground=[("active", BTN_FG)])

    style.configure("Cancel.TButton",
                     background=CANCEL_BG, foreground=CANCEL_FG,
                     font=("monospace", 10), padding=(12, 6),
                     borderwidth=0)
    style.map("Cancel.TButton",
              background=[("active", "#f85149"), ("pressed", "#b62324")],
              foreground=[("active", CANCEL_FG)])

    style.configure("Browse.TButton",
                     background=BG_CARD, foreground=ACCENT,
                     font=("monospace", 9), padding=(8, 4),
                     borderwidth=1, relief="solid")
    style.map("Browse.TButton",
              background=[("active", "#1a2332")],
              foreground=[("active", "#ffffff")])

    # Notebook (tabs)
    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab",
                     background=BG_LIGHT, foreground=FG_DIM,
                     font=("monospace", 10, "bold"), padding=(14, 6))
    style.map("TNotebook.Tab",
              background=[("selected", BG_CARD), ("active", "#1a2332")],
              foreground=[("selected", ACCENT), ("active", FG)])

    # LabelFrame
    style.configure("TLabelframe",
                     background=BG_CARD, foreground=ACCENT,
                     bordercolor=BORDER, relief="solid",
                     font=("monospace", 10, "bold"), padding=8)
    style.configure("TLabelframe.Label",
                     background=BG_CARD, foreground=ACCENT,
                     font=("monospace", 10, "bold"))

    # Separator
    style.configure("TSeparator", background=BORDER)

    # Scrollbar
    style.configure("Vertical.TScrollbar",
                     background=BG_LIGHT, troughcolor=BG,
                     arrowcolor=FG_DIM, bordercolor=BG,
                     relief="flat")
    style.map("Vertical.TScrollbar",
              background=[("active", BORDER)])


def setup_run_with_ui(args: argparse.Namespace) -> bool:
    """Open a setup popup; returns True if the user clicked Start."""
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except Exception:
        logger.warning("UI unavailable: tkinter is not installed")
        return False

    root = tk.Tk()
    root.title("CMD-AUDIO  //  Setup")
    root.resizable(True, True)
    root.minsize(780, 620)
    root.configure(bg="#0d1117")

    # ── Variables ──────────────────────────────────────────────────────
    audio_var = tk.StringVar(value=" ".join(args.audio).strip())
    source_var = tk.StringVar(value=args.source)
    capture_var = tk.StringVar(value=str(args.capture_seconds))
    fps_var = tk.StringVar(value=str(args.fps))
    play_var = tk.BooleanVar(value=args.play)
    seed_var = tk.StringVar(value="" if args.seed is None else str(args.seed))
    sensitivity_var = tk.StringVar(value=str(args.sensitivity))
    speed_min_var = tk.StringVar(value=str(args.speed_min))
    speed_max_var = tk.StringVar(value=str(args.speed_max))
    switch_min_var = tk.StringVar(value=str(args.terminal_switch_min))
    switch_max_var = tk.StringVar(value=str(args.terminal_switch_max))
    theme_var = tk.StringVar(value=args.theme)
    preset_var = tk.StringVar(value=args.preset)
    scene_sync_var = tk.StringVar(value=args.scene_sync)
    quality_var = tk.StringVar(value=args.quality_mode)
    banner_var = tk.StringVar(value=args.banner_text)
    banner_align_var = tk.StringVar(value=args.banner_align)
    banner_anim_var = tk.StringVar(value=args.banner_anim)
    banner_size_var = tk.StringVar(value=args.banner_size)
    show_banner_var = tk.BooleanVar(value=args.show_banner)
    keep_converted_var = tk.BooleanVar(value=args.keep_converted)
    record_file_var = tk.StringVar(value=args.record_file)
    record_mode_var = tk.StringVar(value=args.record_mode)
    youtube_var = tk.StringVar(value=args.youtube)
    playlist_var = tk.StringVar(value=args.playlist)
    scene_pack_var = tk.StringVar(value=args.scene_pack)
    scene_pack_file_var = tk.StringVar(value=args.scene_pack_file)
    plugin_var = tk.StringVar(value=args.plugin)
    video_hook_var = tk.StringVar(value=args.video_hook)
    diagnostics_var = tk.BooleanVar(value=args.diagnostics)
    alert_tones_var = tk.BooleanVar(value=args.alert_tones)
    mission_timeline_var = tk.BooleanVar(value=args.mission_timeline)
    defender_ai_var = tk.BooleanVar(value=args.defender_ai)
    audio_fx_var = tk.BooleanVar(value=args.audio_fx)

    started = [False]

    from cmd_audio.config import SCENE_PACKS, THEMES, PRESETS

    # ── Style ──────────────────────────────────────────────────────────
    style = ttk.Style()
    _apply_dark_theme(root, style)

    # ── Header ─────────────────────────────────────────────────────────
    header_frame = ttk.Frame(root)
    header_frame.pack(fill="x", padx=20, pady=(16, 0))

    ttk.Label(header_frame, text="CMD-AUDIO", style="Header.TLabel").pack(anchor="w")
    ttk.Label(header_frame, text="Configure your run parameters below", style="SubHeader.TLabel").pack(anchor="w", pady=(2, 0))

    # Thin accent line
    sep = tk.Frame(root, height=2, bg="#00ff9f")
    sep.pack(fill="x", padx=20, pady=(8, 0))

    # ── Notebook (tabs) ────────────────────────────────────────────────
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=20, pady=(12, 0))

    # ── Tab: Source & Audio ────────────────────────────────────────────
    tab_source = ttk.Frame(notebook, padding=12)
    notebook.add(tab_source, text="  Source & Audio  ")

    tab_source.columnconfigure(1, weight=1)

    ttk.Label(tab_source, text="Source", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
    source_combo = ttk.Combobox(tab_source, textvariable=source_var, values=["file", "mic", "system"], state="readonly")
    source_combo.grid(row=0, column=1, sticky="ew", pady=4)

    ttk.Label(tab_source, text="YouTube URL", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
    youtube_entry = ttk.Entry(tab_source, textvariable=youtube_var)
    youtube_entry.grid(row=1, column=1, sticky="ew", pady=4)
    
    # YouTube Play button
    def play_youtube():
        """Download and play YouTube audio with random attack patterns."""
        url = youtube_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        
        if "youtube.com" not in url and "youtu.be" not in url:
            messagebox.showerror("Error", "Please enter a valid YouTube URL")
            return
        
        # Set source to file and use YouTube URL
        source_var.set("file")
        args.youtube = url
        args.play = True
        
        # Show downloading message
        messagebox.showinfo("Downloading", "YouTube audio is being downloaded...\nThis may take a moment.")
        
        # Start the run
        _start_run()
    
    ttk.Button(
        tab_source, text="▶ Play YouTube", style="Accent.TButton",
        command=play_youtube,
    ).grid(row=1, column=2, sticky="w", padx=(8, 0), pady=4)

    ttk.Label(tab_source, text="Audio File", style="Field.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
    audio_entry = ttk.Entry(tab_source, textvariable=audio_var)
    audio_entry.grid(row=2, column=1, sticky="ew", pady=4)
    browse_btn = ttk.Button(
        tab_source, text="Browse…", style="Browse.TButton",
        command=lambda: audio_var.set(filedialog.askopenfilename() or audio_var.get()),
    )
    browse_btn.grid(row=2, column=2, sticky="w", padx=(8, 0), pady=4)

    ttk.Label(tab_source, text="Playlist File", style="Field.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(tab_source, textvariable=playlist_var).grid(row=3, column=1, sticky="ew", pady=4)
    ttk.Button(
        tab_source, text="Browse…", style="Browse.TButton",
        command=lambda: playlist_var.set(filedialog.askopenfilename() or playlist_var.get()),
    ).grid(row=3, column=2, sticky="w", padx=(8, 0), pady=4)

    ttk.Label(tab_source, text="Capture Seconds", style="Field.TLabel").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(tab_source, textvariable=capture_var).grid(row=4, column=1, sticky="ew", pady=4)

    ttk.Label(tab_source, text="FPS", style="Field.TLabel").grid(row=5, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(tab_source, textvariable=fps_var).grid(row=5, column=1, sticky="ew", pady=4)

    ttk.Checkbutton(tab_source, text="Play Audio", variable=play_var, style="Check.TCheckbutton").grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 4))

    # ── Tab: Playback ──────────────────────────────────────────────────
    tab_playback = ttk.Frame(notebook, padding=12)
    notebook.add(tab_playback, text="  Playback  ")

    tab_playback.columnconfigure(1, weight=1)

    ttk.Label(tab_playback, text="Sensitivity", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(tab_playback, textvariable=sensitivity_var).grid(row=0, column=1, sticky="ew", pady=4)

    ttk.Label(tab_playback, text="Speed Min", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(tab_playback, textvariable=speed_min_var).grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(tab_playback, text="Speed Max", style="Field.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(tab_playback, textvariable=speed_max_var).grid(row=2, column=1, sticky="ew", pady=4)

    ttk.Label(tab_playback, text="Switch Min (s)", style="Field.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(tab_playback, textvariable=switch_min_var).grid(row=3, column=1, sticky="ew", pady=4)

    ttk.Label(tab_playback, text="Switch Max (s)", style="Field.TLabel").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(tab_playback, textvariable=switch_max_var).grid(row=4, column=1, sticky="ew", pady=4)

    ttk.Label(tab_playback, text="Seed (optional)", style="Field.TLabel").grid(row=5, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(tab_playback, textvariable=seed_var).grid(row=5, column=1, sticky="ew", pady=4)

    # ── Tab: Visual & Theme ────────────────────────────────────────────
    tab_visual = ttk.Frame(notebook, padding=12)
    notebook.add(tab_visual, text="  Visual & Theme  ")

    tab_visual.columnconfigure(1, weight=1)

    ttk.Label(tab_visual, text="Theme", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Combobox(tab_visual, textvariable=theme_var, values=list(THEMES.keys()), state="readonly").grid(row=0, column=1, sticky="ew", pady=4)

    ttk.Label(tab_visual, text="Preset", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Combobox(tab_visual, textvariable=preset_var, values=[""] + list(PRESETS.keys()), state="readonly").grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(tab_visual, text="Scene Sync", style="Field.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Combobox(tab_visual, textvariable=scene_sync_var, values=["adaptive", "bpm", "hybrid"], state="readonly").grid(row=2, column=1, sticky="ew", pady=4)

    ttk.Label(tab_visual, text="Quality", style="Field.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Combobox(tab_visual, textvariable=quality_var, values=["auto", "off"], state="readonly").grid(row=3, column=1, sticky="ew", pady=4)

    ttk.Label(tab_visual, text="Scene Pack", style="Field.TLabel").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Combobox(tab_visual, textvariable=scene_pack_var, values=[""] + sorted(list(SCENE_PACKS.keys())), state="readonly").grid(row=4, column=1, sticky="ew", pady=4)

    ttk.Label(tab_visual, text="Scene Pack File", style="Field.TLabel").grid(row=5, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(tab_visual, textvariable=scene_pack_file_var).grid(row=5, column=1, sticky="ew", pady=4)
    ttk.Button(
        tab_visual, text="Browse…", style="Browse.TButton",
        command=lambda: scene_pack_file_var.set(filedialog.askopenfilename() or scene_pack_file_var.get()),
    ).grid(row=5, column=2, sticky="w", padx=(8, 0), pady=4)

    # ── Tab: Banner ────────────────────────────────────────────────────
    tab_banner = ttk.Frame(notebook, padding=12)
    notebook.add(tab_banner, text="  Banner  ")

    tab_banner.columnconfigure(1, weight=1)

    ttk.Checkbutton(tab_banner, text="Show Banner Row", variable=show_banner_var, style="Check.TCheckbutton").grid(row=0, column=0, columnspan=2, sticky="w", pady=(4, 8))

    ttk.Label(tab_banner, text="Banner Text", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(tab_banner, textvariable=banner_var).grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(tab_banner, text="Banner Align", style="Field.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Combobox(tab_banner, textvariable=banner_align_var, values=["left", "center", "right"], state="readonly").grid(row=2, column=1, sticky="ew", pady=4)

    ttk.Label(tab_banner, text="Banner Animation", style="Field.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Combobox(tab_banner, textvariable=banner_anim_var, values=["off", "scroll", "pulse"], state="readonly").grid(row=3, column=1, sticky="ew", pady=4)

    ttk.Label(tab_banner, text="Banner Size", style="Field.TLabel").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Combobox(tab_banner, textvariable=banner_size_var, values=["normal", "large"], state="readonly").grid(row=4, column=1, sticky="ew", pady=4)

    # ── Tab: Features ──────────────────────────────────────────────────
    tab_features = ttk.Frame(notebook, padding=12)
    notebook.add(tab_features, text="  Features  ")

    tab_features.columnconfigure(0, weight=1)
    tab_features.columnconfigure(1, weight=1)
    tab_features.columnconfigure(2, weight=1)

    ttk.Checkbutton(tab_features, text="Keep Converted WAV", variable=keep_converted_var, style="Check.TCheckbutton").grid(row=0, column=0, sticky="w", pady=4, padx=4)
    ttk.Checkbutton(tab_features, text="Alert Tones", variable=alert_tones_var, style="Check.TCheckbutton").grid(row=0, column=1, sticky="w", pady=4, padx=4)
    ttk.Checkbutton(tab_features, text="Defender AI", variable=defender_ai_var, style="Check.TCheckbutton").grid(row=0, column=2, sticky="w", pady=4, padx=4)

    ttk.Checkbutton(tab_features, text="Print Diagnostics", variable=diagnostics_var, style="Check.TCheckbutton").grid(row=1, column=0, sticky="w", pady=4, padx=4)
    ttk.Checkbutton(tab_features, text="Mission Timeline", variable=mission_timeline_var, style="Check.TCheckbutton").grid(row=1, column=1, sticky="w", pady=4, padx=4)
    ttk.Checkbutton(tab_features, text="Audio FX", variable=audio_fx_var, style="Check.TCheckbutton").grid(row=1, column=2, sticky="w", pady=4, padx=4)

    # ── Tab: Advanced ──────────────────────────────────────────────────
    tab_advanced = ttk.Frame(notebook, padding=12)
    notebook.add(tab_advanced, text="  Advanced  ")

    tab_advanced.columnconfigure(1, weight=1)

    ttk.Label(tab_advanced, text="Record File", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(tab_advanced, textvariable=record_file_var).grid(row=0, column=1, sticky="ew", pady=4)

    ttk.Label(tab_advanced, text="Record Mode", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Combobox(tab_advanced, textvariable=record_mode_var, values=["jsonl", "txt", "txt-clean", "jsonl.gz", "txt.gz", "txt-clean.gz"], state="readonly").grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(tab_advanced, text="Plugin File", style="Field.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(tab_advanced, textvariable=plugin_var).grid(row=2, column=1, sticky="ew", pady=4)
    ttk.Button(
        tab_advanced, text="Browse…", style="Browse.TButton",
        command=lambda: plugin_var.set(filedialog.askopenfilename() or plugin_var.get()),
    ).grid(row=2, column=2, sticky="w", padx=(8, 0), pady=4)

    ttk.Label(tab_advanced, text="Video Hook", style="Field.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(tab_advanced, textvariable=video_hook_var).grid(row=3, column=1, sticky="ew", pady=4)

    # ── Bottom bar (buttons) ───────────────────────────────────────────
    bottom_frame = ttk.Frame(root)
    bottom_frame.pack(fill="x", padx=20, pady=(8, 16))

    # Accent line above buttons
    sep2 = tk.Frame(root, height=1, bg="#30363d")
    sep2.pack(fill="x", padx=20, pady=(0, 0))

    ttk.Button(bottom_frame, text="Cancel", style="Cancel.TButton", command=root.destroy).pack(side="right")
    ttk.Button(bottom_frame, text="▶  Start", style="Accent.TButton", command=lambda: _start_run()).pack(side="right", padx=(0, 10))

    # ── Source state logic ─────────────────────────────────────────────
    def update_source_state(*_: object) -> None:
        in_file_mode = source_var.get() == "file"
        state = "normal" if in_file_mode else "disabled"
        youtube_entry.configure(state=state)
        audio_entry.configure(state=state)
        browse_btn.configure(state=state)

    source_var.trace_add("write", update_source_state)
    update_source_state()

    # ── Start run ──────────────────────────────────────────────────────
    def _start_run() -> None:
        def parse_int_field(raw: str, field_name: str, lo: int, hi: int) -> int:
            try:
                value = int(raw)
            except ValueError as exc:
                raise ValueError(f"{field_name} must be an integer") from exc
            if value < lo or value > hi:
                raise ValueError(f"{field_name} must be between {lo} and {hi}")
            return value

        def parse_float_field(raw: str, field_name: str, lo: float, hi: float) -> float:
            try:
                value = float(raw)
            except ValueError as exc:
                raise ValueError(f"{field_name} must be a number") from exc
            if value < lo or value > hi:
                raise ValueError(f"{field_name} must be between {lo:.2f} and {hi:.2f}")
            return value

        try:
            source = source_var.get().strip()
            if source not in ("file", "mic", "system"):
                raise ValueError("Source must be file, mic, or system")

            youtube_url = youtube_var.get().strip()
            audio_path = audio_var.get().strip()
            playlist_path = playlist_var.get().strip()
            if source == "file" and not youtube_url and not audio_path and not playlist_path:
                messagebox.showerror("Missing Audio", "YouTube URL, audio file path, or playlist file is required when source is file.")
                return

            args.source = source
            args.youtube = youtube_url
            args.audio = [audio_path] if audio_path else []
            args.capture_seconds = parse_int_field(capture_var.get(), "Capture Seconds", 1, 3600)
            args.fps = parse_int_field(fps_var.get(), "FPS", 1, 240)
            args.play = bool(play_var.get())

            seed_text = seed_var.get().strip()
            args.seed = parse_int_field(seed_text, "Seed", -2147483648, 2147483647) if seed_text else None

            args.sensitivity = parse_float_field(sensitivity_var.get(), "Sensitivity", 0.1, 4.0)
            args.speed_min = parse_float_field(speed_min_var.get(), "Speed Min", 0.05, 6.0)
            args.speed_max = parse_float_field(speed_max_var.get(), "Speed Max", args.speed_min, 6.0)
            args.terminal_switch_min = parse_float_field(switch_min_var.get(), "Switch Min", 0.5, 60.0)
            args.terminal_switch_max = parse_float_field(switch_max_var.get(), "Switch Max", args.terminal_switch_min, 60.0)
            args.theme = theme_var.get().strip() if theme_var.get().strip() in THEMES else "matrix"
            args.preset = preset_var.get().strip() if preset_var.get().strip() in PRESETS else ""
            args.scene_sync = scene_sync_var.get().strip() if scene_sync_var.get().strip() in ("adaptive", "bpm", "hybrid") else "adaptive"
            args.quality_mode = quality_var.get().strip() if quality_var.get().strip() in ("auto", "off") else "auto"
            args.banner_text = banner_var.get()
            args.banner_align = banner_align_var.get().strip() if banner_align_var.get().strip() in ("left", "center", "right") else "center"
            args.banner_anim = banner_anim_var.get().strip() if banner_anim_var.get().strip() in ("off", "scroll", "pulse") else "off"
            args.banner_size = banner_size_var.get().strip() if banner_size_var.get().strip() in ("normal", "large") else "normal"
            args.show_banner = bool(show_banner_var.get())
            args.keep_converted = bool(keep_converted_var.get())
            args.record_file = record_file_var.get().strip()
            args.record_mode = record_mode_var.get().strip() if record_mode_var.get().strip() in ("jsonl", "txt", "txt-clean", "jsonl.gz", "txt.gz", "txt-clean.gz") else "jsonl"
            args.playlist = playlist_path
            args.scene_pack = scene_pack_var.get().strip()
            args.scene_pack_file = scene_pack_file_var.get().strip()
            args.plugin = plugin_var.get().strip()
            args.video_hook = video_hook_var.get().strip()
            args.diagnostics = bool(diagnostics_var.get())
            args.alert_tones = bool(alert_tones_var.get())
            args.mission_timeline = bool(mission_timeline_var.get())
            args.defender_ai = bool(defender_ai_var.get())
            args.audio_fx = bool(audio_fx_var.get())
        except ValueError as exc:
            messagebox.showerror("Invalid Input", str(exc))
            return

        started[0] = True
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", root.destroy)

    _setup_vars = (
        audio_var, source_var, capture_var, fps_var, play_var, seed_var,
        sensitivity_var, speed_min_var, speed_max_var, switch_min_var, switch_max_var,
        theme_var, preset_var, scene_sync_var, quality_var,
        banner_var, banner_align_var, banner_anim_var, banner_size_var, show_banner_var,
        keep_converted_var, record_file_var, record_mode_var,
        playlist_var, scene_pack_var, scene_pack_file_var, plugin_var, video_hook_var,
        diagnostics_var,
        alert_tones_var, mission_timeline_var, defender_ai_var, audio_fx_var,
    )
    root.mainloop()

    for _var in _setup_vars:
        try:
            _var._tk = None  # type: ignore[attr-defined]
        except Exception:
            pass

    return started[0]