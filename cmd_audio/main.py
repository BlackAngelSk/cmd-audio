"""Argument parsing and main render loop."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import re
import shutil
import signal
import subprocess
import sys
import time
import wave
from typing import Any, Dict, List, Optional

import cmd_audio.config as _cfg
from cmd_audio.config import (
    HACKNET_OPERATIONS,
    MISSION_PHASES,
    OPERATION_MODES,
    PRESETS,
    SCENE_PACKS,
    TARGETS,
    TERMINAL_PROFILES,
    THEMES,
    THEME_MODES,
    apply_theme,
    set_bar_mode,
    set_theme_mode,
    set_bass_threshold,
    CURRENT_THEME_MODE,
    BASS_THRESHOLD,
)
from cmd_audio.utils import clamp, fit_text
from cmd_audio.terminal import RawInput
from cmd_audio.audio import AudioFeatures, make_demo_audio_features, read_audio_features
from cmd_audio.audio_input import prepare_audio_input, get_random_attack_pattern, is_youtube_url
from cmd_audio.effects import (
    apply_terminal_fx,
    build_banner_lines,
    meter_bar,
    make_log_line,
    make_incident_line,
    panel_box,
    prompt_banner_text,
)
from cmd_audio.visual import (
    VisualState,
    ALL_VISUAL_MODULES,
    build_telemetry_lines,
    compose_center_panel,
    generate_shell_feed,
    get_visual_modules_for_cycle,
    refresh_visual_state,
    render_paneled_visuals,
)
from cmd_audio.record import open_record_writer, write_record_frame, load_replay_frames
from cmd_audio.mission import (
    IncidentFeedState,
    maybe_apply_defender_countermeasure,
    mission_timeline_from_progress,
    should_shift_scene,
)
from cmd_audio.control import LiveControlState, LiveUIHandle, start_live_control_window
from cmd_audio.logging_config import setup_logging, get_logger
from cmd_audio.web_server import start_web_server, AudioServer
from cmd_audio.remote_control import create_remote_control

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Config / JSON helpers
# ---------------------------------------------------------------------------

def parse_json_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("config root must be a JSON object")
    return data


def load_scene_packs(path: str) -> Dict[str, Dict[str, Any]]:
    data = parse_json_file(path)
    packs = data.get("scene_packs")
    if not isinstance(packs, dict):
        raise ValueError("scene pack file must contain object key 'scene_packs'")
    out: Dict[str, Dict[str, Any]] = {}
    for name, cfg in packs.items():
        if isinstance(name, str) and isinstance(cfg, dict):
            out[name] = cfg
    if not out:
        raise ValueError("scene pack file has no valid packs")
    return out


def apply_scene_pack(args: argparse.Namespace, pack: Dict[str, Any]) -> Dict[str, float]:
    if isinstance(pack.get("scene_sync"), str) and pack["scene_sync"] in ("adaptive", "bpm", "hybrid"):
        args.scene_sync = str(pack["scene_sync"])
    if isinstance(pack.get("quality_mode"), str) and pack["quality_mode"] in ("off", "auto"):
        args.quality_mode = str(pack["quality_mode"])
    if isinstance(pack.get("ui_style"), str) and pack["ui_style"] in ("full", "minimal"):
        args.ui_style = str(pack["ui_style"])

    defaults = {"nodes": 1.0, "files": 1.0, "firewall": 1.0, "ports": 1.0, "crypto": 1.0, "admin": 1.0}
    raw_weights = pack.get("module_weights") if isinstance(pack.get("module_weights"), dict) else {}
    weights = dict(defaults)
    if isinstance(raw_weights, dict):
        for key in defaults:
            v = raw_weights.get(key)
            if isinstance(v, (float, int)):
                weights[key] = clamp(float(v), 0.4, 1.8)
    return weights


def load_playlist_file(path: str) -> List[str]:
    tracks: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if os.path.exists(line):
                tracks.append(line)
    if not tracks:
        raise ValueError("Playlist has no valid audio paths")
    return tracks


def load_plugin_module(path: str) -> Any:
    if not os.path.exists(path):
        raise ValueError(f"Plugin file not found: {path}")
    mod_name = f"cmd_audio_plugin_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ValueError("Could not load plugin spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize_theme(value: Any) -> Optional[str]:
    if isinstance(value, str) and value in THEMES:
        return value
    return None


def merge_args_with_config(argv: List[str], config_data: Dict[str, Any]) -> List[str]:
    out = list(argv)
    cli_text = " ".join(argv)

    if not any(not a.startswith("-") for a in argv):
        audio_val = config_data.get("audio")
        if isinstance(audio_val, str) and audio_val.strip():
            out.insert(0, audio_val.strip())

    mapping = {
        "source": "--source", "capture_seconds": "--capture-seconds", "fps": "--fps",
        "seed": "--seed", "sensitivity": "--sensitivity", "speed_min": "--speed-min",
        "speed_max": "--speed-max", "terminal_switch_min": "--terminal-switch-min",
        "terminal_switch_max": "--terminal-switch-max", "theme": "--theme",
        "banner_text": "--banner-text", "banner_align": "--banner-align",
        "banner_anim": "--banner-anim", "banner_size": "--banner-size",
        "record_file": "--record-file", "record_mode": "--record-mode",
        "video_hook": "--video-hook", "plugin": "--plugin", "replay_file": "--replay-file",
        "preset": "--preset", "scene_sync": "--scene-sync", "quality_mode": "--quality-mode",
        "ui_style": "--ui-style", "scene_pack": "--scene-pack", "scene_pack_file": "--scene-pack-file",
        "playlist": "--playlist", "alert_tones": "--alert-tones",
        "mission_timeline": "--mission-timeline", "defender_ai": "--defender-ai",
        "audio_fx": "--audio-fx", "setup_ui": "--setup-ui",
    }
    for key, flag in mapping.items():
        if flag in cli_text:
            continue
        if key not in config_data:
            continue
        value = config_data[key]
        if isinstance(value, bool):
            if value:
                out.append(flag)
        elif value is not None:
            out.extend([flag, str(value)])

    neg_flags = {
        "play": "--mute", "ui": "--no-ui", "mission_timeline": "--no-mission-timeline",
        "defender_ai": "--no-defender-ai", "audio_fx": "--no-audio-fx", "setup_ui": "--no-setup-ui",
    }
    for bool_key, flag in (("play", "--play"), ("keep_converted", "--keep-converted"), ("ui", "--ui"), ("show_banner", "--show-banner"), ("diagnostics", "--diagnostics"), ("unicode_bars", "--unicode-bars"), ("mission_timeline", "--mission-timeline"), ("defender_ai", "--defender-ai"), ("audio_fx", "--audio-fx"), ("setup_ui", "--setup-ui")):
        neg_flag = neg_flags.get(bool_key, "")
        if flag in cli_text or (neg_flag and neg_flag in cli_text):
            continue
        cfg_val = config_data.get(bool_key)
        if cfg_val is True:
            out.append(flag)
        elif cfg_val is False and neg_flag:
            out.append(neg_flag)

    return out


def apply_preset(args: argparse.Namespace, preset_name: str) -> None:
    preset = PRESETS.get(preset_name)
    if not preset:
        raise ValueError(f"Unknown preset: {preset_name}")
    for key, value in preset.items():
        setattr(args, key, value)


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

def print_diagnostics(args: argparse.Namespace, audio_path: str, playback_path: str, audio: Optional[AudioFeatures]) -> None:
    term = shutil.get_terminal_size(fallback=(100, 30))
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    ffplay_ok = shutil.which("ffplay") is not None
    aplay_ok = shutil.which("aplay") is not None
    bpm = f"{audio.bpm_estimate:.1f}" if audio is not None and audio.bpm_estimate > 0 else "n/a"
    duration = f"{audio.duration:.2f}s" if audio is not None else "n/a"
    logger.debug("source=%s", args.source)
    logger.debug("audio=%s", audio_path or "(none)")
    logger.debug("playback=%s", playback_path or "(none)")
    logger.debug("fps=%s terminal=%sx%s", args.fps, term.columns, term.lines)
    logger.debug("ffmpeg=%s ffplay=%s aplay=%s", ffmpeg_ok, ffplay_ok, aplay_ok)
    logger.debug("duration=%s bpm=%s", duration, bpm)


# ---------------------------------------------------------------------------
# Audio player
# ---------------------------------------------------------------------------

def launch_player(path: str) -> "subprocess.Popen[bytes] | None":
    players = [
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", path],
        ["aplay", path],
    ]
    for cmd in players:
        try:
            return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            continue
    return None


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Music-synced terminal hacker effect")
    p.add_argument("--config", default="", help="Optional JSON config path")
    p.add_argument("--save-config", default="", help="Write current settings to JSON and exit")
    p.add_argument("audio", nargs="*", help="Audio path (supports unquoted spaces)")
    p.add_argument("--source", choices=["file", "mic", "system"], default="file")
    p.add_argument("--youtube", default="", help="YouTube URL to download and play")
    p.add_argument("--playlist", default="", help="Optional text playlist (one path per line)")
    p.add_argument("--capture-seconds", type=int, default=30, help="Seconds to capture for mic/system")
    p.add_argument("--fps", type=int, default=30, help="Frames per second")
    p.add_argument("--play", dest="play", action="store_true", help="Play audio during render")
    p.add_argument("--mute", dest="play", action="store_false", help="Disable audio playback")
    p.add_argument("--seed", type=int, default=None, help="Random seed")
    p.add_argument("--sensitivity", type=float, default=1.0, help="Visual intensity multiplier")
    p.add_argument("--speed-min", type=float, default=0.25, help="Minimum visual speed")
    p.add_argument("--speed-max", type=float, default=3.0, help="Maximum visual speed")
    p.add_argument("--terminal-switch-min", type=float, default=4.0, help="Minimum seconds before switching terminal type")
    p.add_argument("--terminal-switch-max", type=float, default=11.0, help="Maximum seconds before switching terminal type")
    p.add_argument("--theme", choices=list(THEMES.keys()), default="matrix")
    p.add_argument("--theme-mode", choices=THEME_MODES, default="manual", help="Dynamic theme switching: manual or bass")
    p.add_argument("--bass-threshold", type=float, default=0.15, help="Bass spike threshold for theme switching (0.01-1.0)")
    p.add_argument("--banner-text", default="", help="Optional text banner to show in the output")
    p.add_argument("--banner-align", choices=["left", "center", "right"], default="center")
    p.add_argument("--banner-anim", choices=["off", "scroll", "pulse"], default="off")
    p.add_argument("--banner-size", choices=["normal", "large"], default="normal")
    p.add_argument("--show-banner", action="store_true", help="Show banner line even if banner text is empty")
    p.add_argument("--keep-converted", action="store_true", help="Keep temporary WAV conversion")
    p.add_argument("--record-file", default="", help="Optional JSONL frame recording path")
    p.add_argument("--record-mode", choices=["jsonl", "txt", "txt-clean", "jsonl.gz", "txt.gz", "txt-clean.gz"], default="jsonl")
    p.add_argument("--video-hook", default="", help="Optional shell command run after recording finishes")
    p.add_argument("--plugin", default="", help="Optional Python plugin file with hooks")
    p.add_argument("--replay-file", default="", help="Replay frames from a previous recording file")
    p.add_argument("--preset", choices=list(PRESETS.keys()), default="", help="Apply a visual preset")
    p.add_argument("--scene-sync", choices=["adaptive", "bpm", "hybrid"], default="adaptive")
    p.add_argument("--quality-mode", choices=["off", "auto"], default="auto")
    p.add_argument("--ui-style", choices=["full", "minimal"], default="full")
    p.add_argument("--scene-pack", default="", help="Named scene pack")
    p.add_argument("--scene-pack-file", default="", help="JSON file with custom scene packs")
    p.add_argument("--save-scene-pack", default="", help="Write current active scene pack to JSON and exit")
    p.add_argument("--unicode-bars", action="store_true", help="Use Unicode block bars for meters")
    p.add_argument("--alert-tones", action="store_true", help="Enable event-linked terminal alert tones")
    p.add_argument("--mission-timeline", dest="mission_timeline", action="store_true")
    p.add_argument("--no-mission-timeline", dest="mission_timeline", action="store_false")
    p.add_argument("--defender-ai", dest="defender_ai", action="store_true")
    p.add_argument("--no-defender-ai", dest="defender_ai", action="store_false")
    p.add_argument("--audio-fx", dest="audio_fx", action="store_true")
    p.add_argument("--no-audio-fx", dest="audio_fx", action="store_false")
    p.add_argument("--diagnostics", action="store_true", help="Print startup diagnostics to stderr")
    p.add_argument("--setup-ui", dest="setup_ui", action="store_true")
    p.add_argument("--no-setup-ui", dest="setup_ui", action="store_false")
    p.add_argument("--ui", dest="ui", action="store_true")
    p.add_argument("--no-ui", dest="ui", action="store_false")
    p.add_argument("--web", dest="web", action="store_true", help="Start web server for browser visualization")
    p.add_argument("--web-port", type=int, default=8080, help="Web server port")
    p.add_argument("--web-host", default="localhost", help="Web server host")
    p.add_argument("--remote-control", dest="remote_control", action="store_true", help="Enable remote control socket")
    p.add_argument("--remote-port", type=int, default=9999, help="Remote control port")
    p.add_argument("--normalize", action="store_true", help="Normalize audio levels across tracks")
    p.set_defaults(play=True, ui=True, mission_timeline=True, defender_ai=True, audio_fx=True, setup_ui=False, web=False, remote_control=False, normalize=False)
    first_pass = p.parse_known_args()[0]

    argv = sys.argv[1:]
    if first_pass.config:
        cfg = parse_json_file(first_pass.config)
        argv = merge_args_with_config(argv, cfg)

    args = p.parse_args(argv)
    if args.preset:
        apply_preset(args, args.preset)
    if normalize_theme(args.theme) is None:
        args.theme = "matrix"
    if args.theme_mode not in THEME_MODES:
        args.theme_mode = "manual"
    set_theme_mode(args.theme_mode)
    set_bass_threshold(args.bass_threshold)
    return args


# ---------------------------------------------------------------------------
# Screen clear
# ---------------------------------------------------------------------------

def clear_and_home() -> None:
    sys.stdout.write(_cfg.CLEAR)
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> int:
    from cmd_audio.ui_setup import setup_run_with_ui

    # Initialize logging based on diagnostics flag
    verbosity = 2 if getattr(parse_args(), 'diagnostics', False) else 1
    setup_logging(verbosity=verbosity)

    args = parse_args()

    # Re-setup logging with correct verbosity after args parsing
    setup_logging(verbosity=2 if args.diagnostics else 1)

    if args.setup_ui:
        # Automatically enable live controls when setup UI is used
        args.ui = True
        started = setup_run_with_ui(args)
        if not started:
            return 0

    plugin_module: Any = None
    if args.plugin:
        try:
            plugin_module = load_plugin_module(args.plugin)
        except Exception as exc:
            logger.error("Plugin error: %s", exc)
            return 1

    custom_scene_packs: Dict[str, Dict[str, Any]] = {}
    if args.scene_pack_file:
        try:
            custom_scene_packs = load_scene_packs(args.scene_pack_file)
        except (OSError, ValueError) as exc:
            logger.error("Scene pack error: %s", exc)
            return 1

    active_scene_pack_name = args.scene_pack.strip()
    all_scene_packs = dict(SCENE_PACKS)
    all_scene_packs.update(custom_scene_packs)
    scene_pack_weights = {"nodes": 1.0, "files": 1.0, "firewall": 1.0, "ports": 1.0, "crypto": 1.0, "admin": 1.0, "processes": 1.0, "traffic": 1.0, "syslog": 1.0, "filesystem": 1.0, "ssh-brute": 1.0, "dns": 1.0, "db-dump": 1.0, "memory": 1.0}

    if active_scene_pack_name:
        chosen_pack = all_scene_packs.get(active_scene_pack_name)
        if chosen_pack is None:
            logger.error("Unknown scene pack: %s", active_scene_pack_name)
            return 1
        scene_pack_weights = apply_scene_pack(args, chosen_pack)

    if args.save_config:
        config_payload = {
            "audio": " ".join(args.audio).strip(), "source": args.source, "playlist": args.playlist,
            "capture_seconds": args.capture_seconds, "fps": args.fps, "play": args.play, "seed": args.seed,
            "sensitivity": args.sensitivity, "speed_min": args.speed_min, "speed_max": args.speed_max,
            "terminal_switch_min": args.terminal_switch_min, "terminal_switch_max": args.terminal_switch_max,
            "theme": args.theme, "preset": args.preset, "scene_sync": args.scene_sync,
            "quality_mode": args.quality_mode, "ui_style": args.ui_style,
            "scene_pack": active_scene_pack_name, "scene_pack_file": args.scene_pack_file,
            "unicode_bars": args.unicode_bars, "alert_tones": args.alert_tones,
            "mission_timeline": args.mission_timeline, "defender_ai": args.defender_ai, "audio_fx": args.audio_fx,
            "banner_text": args.banner_text, "banner_align": args.banner_align,
            "banner_anim": args.banner_anim, "banner_size": args.banner_size, "show_banner": args.show_banner,
            "keep_converted": args.keep_converted, "record_file": args.record_file, "record_mode": args.record_mode,
            "video_hook": args.video_hook, "plugin": args.plugin, "setup_ui": args.setup_ui, "ui": args.ui,
            "diagnostics": args.diagnostics,
        }
        with open(args.save_config, "w", encoding="utf-8") as f:
            json.dump(config_payload, f, indent=2)
        print(f"Saved config to: {args.save_config}")
        return 0

    if args.save_scene_pack:
        payload = {
            "scene_packs": {
                (active_scene_pack_name or "exported"): {
                    "scene_sync": args.scene_sync, "quality_mode": args.quality_mode,
                    "ui_style": args.ui_style, "module_weights": scene_pack_weights,
                }
            }
        }
        with open(args.save_scene_pack, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"Saved scene pack to: {args.save_scene_pack}")
        return 0

    theme_name = apply_theme(args.theme)
    set_bar_mode(args.unicode_bars)
    live_state: Optional[LiveControlState] = None
    live_ui: Optional[LiveUIHandle] = None
    web_server: Optional[AudioServer] = None
    initial_music_file = args.youtube or " ".join(args.audio).strip() or "(demo mode)"

    def close_live_ui() -> None:
        if live_ui is not None:
            live_ui.close()

    args.terminal_switch_min = clamp(args.terminal_switch_min, 0.5, 60.0)
    args.terminal_switch_max = clamp(args.terminal_switch_max, args.terminal_switch_min, 60.0)
    if args.ui:
        live_state = LiveControlState(
            args.sensitivity, args.speed_min, args.speed_max,
            args.terminal_switch_min, args.terminal_switch_max,
            theme_name, args.theme_mode, args.banner_text, args.banner_align, args.banner_anim, args.banner_size,
            bool(args.show_banner), args.ui_style, args.quality_mode, bool(args.unicode_bars),
            args.scene_sync, bool(args.alert_tones), bool(args.mission_timeline),
            bool(args.defender_ai), bool(args.audio_fx),
            "netrunner", OPERATION_MODES[0], TARGETS[0], False, initial_music_file,
        )

    # Start web server if requested
    if args.web:
        try:
            web_server = start_web_server(host=args.web_host, port=args.web_port)
            logger.info("Web server started at http://%s:%d", args.web_host, args.web_port)
        except Exception as exc:
            logger.error("Failed to start web server: %s", exc)

    # Start remote control socket if requested
    remote_sock = None
    if args.remote_control:
        try:
            remote_sock = create_remote_control()
            remote_sock.start()
            logger.info("Remote control socket started at %s", remote_sock.socket_path)
        except Exception as exc:
            logger.error("Failed to start remote control: %s", exc)

    if args.seed is not None:
        random.seed(args.seed)

    if args.replay_file:
        try:
            replay_frames = load_replay_frames(args.replay_file)
        except (OSError, ValueError) as exc:
            logger.error("Replay error: %s", exc)
            close_live_ui()
            return 1
        raw = RawInput()
        raw.enable()
        sys.stdout.write(_cfg.SHOW_CURSOR)
        clear_and_home()
        frame_time = 1.0 / max(1, args.fps)
        replay_idx = 0
        paused_replay = False
        replay_speed = 1.0
        replay_step = max(1, int(args.fps * 5))
        try:
            while replay_idx < len(replay_frames):
                key = raw.read_key()
                if key == "q":
                    break
                if key == "p":
                    paused_replay = not paused_replay
                if key == ".":
                    paused_replay = True
                    replay_idx = min(len(replay_frames) - 1, replay_idx + 1)
                if key == ",":
                    paused_replay = True
                    replay_idx = max(0, replay_idx - 1)
                if key == "]":
                    replay_speed = min(4.0, replay_speed + 0.25)
                if key == "[":
                    replay_speed = max(0.25, replay_speed - 0.25)
                if key == "f":
                    replay_idx = min(len(replay_frames) - 1, replay_idx + replay_step)
                if key == "b":
                    replay_idx = max(0, replay_idx - replay_step)

                frame = replay_frames[replay_idx]
                sys.stdout.write("\033[H\033[J")
                sys.stdout.write(frame)
                status = f"\n{_cfg.GREEN_DIM}replay: idx={replay_idx + 1}/{len(replay_frames)} speed={replay_speed:.2f}x {'PAUSED' if paused_replay else 'PLAY'} keys:q p . , [ ] f b{_cfg.RESET}"
                sys.stdout.write(status)
                sys.stdout.flush()
                if paused_replay:
                    time.sleep(0.03)
                    continue
                time.sleep(frame_time / replay_speed)
                replay_idx += 1
        finally:
            raw.disable()
            sys.stdout.write(_cfg.SHOW_CURSOR + _cfg.RESET + "\n")
            sys.stdout.flush()
            close_live_ui()
        return 0

    audio_path = " ".join(args.audio).strip()
    if args.youtube:
        audio_path = args.youtube

    playlist_tracks: List[str] = []
    playlist_index = -1

    if args.source == "file":
        if args.playlist:
            try:
                playlist_tracks = load_playlist_file(args.playlist)
            except (OSError, ValueError) as exc:
                logger.error("Playlist error: %s", exc)
                close_live_ui()
                return 1
        elif audio_path:
            playlist_tracks = [audio_path]

        if playlist_tracks:
            if audio_path and audio_path in playlist_tracks:
                playlist_index = playlist_tracks.index(audio_path)
            else:
                playlist_index = 0
                audio_path = playlist_tracks[0]

    cleanup_wav = False
    wav_input = ""
    playback_input = ""
    if args.source == "file" and not audio_path:
        audio = make_demo_audio_features(args.fps, seconds=max(120, args.capture_seconds))
        audio_path = "(demo mode)"
    else:
        try:
            wav_input, playback_input, cleanup_wav = prepare_audio_input(args, audio_path)
        except RuntimeError as exc:
            logger.error("%s", exc)
            close_live_ui()
            return 1

        try:
            audio = read_audio_features(wav_input, args.fps)
        except KeyboardInterrupt:
            logger.warning("Interrupted during audio analysis.")
            close_live_ui()
            if cleanup_wav:
                try:
                    os.unlink(wav_input)
                except OSError:
                    pass
            return 130
        except (wave.Error, ValueError) as exc:
            logger.error("Failed to read audio: %s", exc)
            close_live_ui()
            return 1

    if args.diagnostics:
        print_diagnostics(args, audio_path, playback_input, audio)

    player = launch_player(playback_input) if args.play and playback_input else None

    running = True
    paused = False

    def stop_handler(signum: int, frame: object) -> None:
        del signum, frame
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    rec = None
    if args.record_file:
        try:
            rec = open_record_writer(args.record_file, args.record_mode)
        except (OSError, ValueError) as exc:
            logger.error("Record error: %s", exc)
            close_live_ui()
            return 1

    raw = RawInput()
    raw.enable()

    sys.stdout.write("\033[?25l")
    clear_and_home()

    start = time.perf_counter()
    frame_time = 1.0 / max(1, args.fps)

    logs: List[str] = [
        " 000.00s Boot      CONSOLE  pwr=00%",
        " 000.01s Route     MATRIX   pwr=00%",
        " 000.02s Cipher    PRIME    pwr=00%",
    ]
    history: List[float] = []
    pulse = 0
    prev_level = 0.0
    visual_t = 0.0
    log_budget = 0.0
    hist_budget = 0.0
    dropped_frames = 0
    sensitivity = args.sensitivity
    banner_text = args.banner_text
    current_level = 0.0
    terminal_modes = list(TERMINAL_PROFILES.keys())
    terminal_mode = random.choice(terminal_modes)
    next_terminal_switch_at = random.uniform(args.terminal_switch_min, args.terminal_switch_max)
    operation_modes = OPERATION_MODES
    operation_mode = random.choice(operation_modes)
    target_lock = random.choice(TARGETS)
    net_state = "UPLINK STABLE"
    daemon = random.choice(["sshd", "postfix", "nginx", "xrdp", "redis"])
    clearance = "L1"
    open_ports = random.randint(2, 16)
    trace_hops = random.randint(3, 12)
    packet = random.randint(1200, 9000)
    shell_lines = generate_shell_feed(0.0, False, terminal_mode)
    next_scene_shift_at = random.uniform(1.0, 3.0)
    next_shell_refresh_at = random.uniform(0.4, 1.2)
    bpm_interval = (60.0 / audio.bpm_estimate) if audio.bpm_estimate > 0 else 0.0
    next_bpm_tick_at = bpm_interval if bpm_interval > 0 else 0.0
    show_banner = bool(args.show_banner)
    banner_align = args.banner_align
    banner_anim = args.banner_anim
    banner_size = args.banner_size
    lock_scene = False
    visual_state = VisualState(
        node_rows=[], file_rows=[],
        firewall_state=random.choice(["OFFLINE", "FIREWALL_ACTIVE", "ICE_DETECTED", "WALL_BREACH", "FIREWALL_DOWN"]),
        crypto_algo=random.choice(["RSA-2048", "AES-256", "MD5-LEGACY", "SHA-512", "ECC-384", "DES-OLD"]),
        port_rows=[], admin_rows=[], last_refresh=0.0,
    )

    keys_line = "keys: q p +/- [ ] t b e c v x m r z 0 n u 1 2 3 a y k j g h o l w d D"
    mission_phase_name = MISSION_PHASES[0]["name"]
    mission_objective = MISSION_PHASES[0]["objective"]
    mission_phase_idx = 0
    defender_state = "stable"
    defender_pressure = 1.0
    glitch_frames = 0
    scanline_flash = 0
    jitter = 0
    mission_timeline_enabled = bool(args.mission_timeline)
    defender_ai_enabled = bool(args.defender_ai)
    audio_fx_enabled = bool(args.audio_fx)
    alert_tones_enabled = bool(args.alert_tones)
    incident_feed = IncidentFeedState(host=TARGETS[0], phase=0, ttl=0)
    tone_cooldown_until = 0.0

    theme_order = list(THEMES.keys())
    theme_mode = args.theme_mode

    # Bass detection state
    bass_history: list = []
    last_bass_switch_at = 0.0  # visual_t timestamp of last bass-triggered switch
    BASS_COOLDOWN = 0.8  # seconds between theme switches

    # Visual module cycling state
    visual_module_cycle_idx = 0
    active_visual_modules = get_visual_modules_for_cycle(visual_module_cycle_idx)
    next_visual_module_switch_at = random.uniform(3.0, 8.0)
    visual_module_switch_interval = 5.0  # seconds between auto-switches

    if live_state is not None:
        live_state.set_scene_sync(args.scene_sync)
        live_state.set_ui_style(args.ui_style)
        live_state.set_quality_mode(args.quality_mode)
        live_state.set_unicode_bars(args.unicode_bars)
        live_state.set_show_banner(show_banner)
        live_state.set_banner_align(banner_align)
        live_state.set_banner_anim(banner_anim)
        live_state.set_banner_size(banner_size)
        live_state.set_terminal_mode(terminal_mode)
        live_state.set_operation_mode(operation_mode)
        live_state.set_target_lock(target_lock)
        live_state.set_alert_tones(alert_tones_enabled)
        live_state.set_mission_timeline(mission_timeline_enabled)
        live_state.set_defender_ai(defender_ai_enabled)
        live_state.set_audio_fx(audio_fx_enabled)
        live_state.set_music_file(audio_path)

    def switch_music_file(new_music_path: str, preserve_session: bool = False) -> None:
        nonlocal audio, wav_input, playback_input, cleanup_wav, player
        nonlocal start, visual_t, prev_level, pulse, history, logs
        nonlocal next_bpm_tick_at, bpm_interval, target_lock, operation_mode
        nonlocal net_state, shell_lines, audio_path

        new_music = new_music_path.strip()
        if not new_music:
            return
        
        # Check if it's a YouTube URL
        from cmd_audio.audio_input import is_youtube_url
        if not is_youtube_url(new_music) and not os.path.exists(new_music):
            raise RuntimeError("Selected music file does not exist")

        prev_source = args.source
        args.source = "file"
        try:
            new_wav_input, new_playback_input, new_cleanup_wav = prepare_audio_input(args, new_music)
            new_audio = read_audio_features(new_wav_input, args.fps)
        except Exception:
            args.source = prev_source
            raise

        if player and player.poll() is None:
            player.terminate()
        player = launch_player(new_playback_input) if args.play and new_playback_input else None

        if cleanup_wav:
            try:
                os.unlink(wav_input)
            except OSError:
                pass

        args.audio = [new_music]
        audio_path = new_music
        audio = new_audio
        wav_input = new_wav_input
        playback_input = new_playback_input
        cleanup_wav = new_cleanup_wav
        bpm_interval = (60.0 / audio.bpm_estimate) if audio.bpm_estimate > 0 else 0.0
        next_bpm_tick_at = bpm_interval if bpm_interval > 0 else 0.0

        start = time.perf_counter()
        if not preserve_session:
            visual_t = 0.0
            prev_level = 0.0
            pulse = 0
            history.clear()
            logs = [" 000.00s Boot      CONSOLE  pwr=00%", " 000.01s Route     MATRIX   pwr=00%", " 000.02s Cipher    PRIME    pwr=00%"]
            target_lock = random.choice(TARGETS)
            operation_mode = random.choice(operation_modes)
            net_state = "UPLINK STABLE"
            shell_lines = generate_shell_feed(0.0, False, terminal_mode)
        else:
            logs.append(f" {visual_t:06.2f}s Track     SWITCH   -> {os.path.basename(new_music)}")

        if live_state is not None:
            live_state.set_music_file(new_music)
            live_state.set_music_status("Loaded successfully")

    def advance_playlist(step: int) -> bool:
        nonlocal playlist_index, audio_path
        if not playlist_tracks:
            return False
        next_idx = playlist_index + step
        if next_idx < 0 or next_idx >= len(playlist_tracks):
            return False
        playlist_index = next_idx
        next_track = playlist_tracks[playlist_index]
        try:
            switch_music_file(next_track, preserve_session=True)
        except Exception as exc:
            if live_state is not None:
                live_state.set_music_status(f"Load failed: {exc}")
            return False
        audio_path = next_track
        return True

    # Random attack pattern for YouTube
    current_attack_pattern = None
    attack_pattern_timer = 0.0
    ui_started = False
    try:
        while running:
            if live_state is not None:
                snap = live_state.snapshot()
                if snap.quit_requested:
                    break
                paused = snap.paused
                sensitivity = snap.sensitivity
                args.speed_min = snap.speed_min
                args.speed_max = snap.speed_max
                args.terminal_switch_min = snap.terminal_switch_min
                args.terminal_switch_max = snap.terminal_switch_max
                args.scene_sync = snap.scene_sync
                args.ui_style = snap.ui_style
                args.quality_mode = snap.quality_mode
                show_banner = snap.show_banner
                banner_align = snap.banner_align
                banner_anim = snap.banner_anim
                banner_size = snap.banner_size
                lock_scene = snap.lock_scene
                if snap.theme_name != theme_name:
                    theme_name = apply_theme(snap.theme_name)
                if snap.theme_mode != theme_mode:
                    theme_mode = snap.theme_mode
                    set_theme_mode(theme_mode)
                if snap.unicode_bars != (not _cfg.USE_UNICODE_BARS):
                    set_bar_mode(snap.unicode_bars)
                if snap.terminal_mode in terminal_modes and snap.terminal_mode != terminal_mode:
                    terminal_mode = snap.terminal_mode
                    shell_lines = generate_shell_feed(current_level, False, terminal_mode)
                if snap.operation_mode in operation_modes:
                    operation_mode = snap.operation_mode
                if snap.target_lock in TARGETS:
                    target_lock = snap.target_lock
                alert_tones_enabled = snap.alert_tones
                mission_timeline_enabled = snap.mission_timeline
                defender_ai_enabled = snap.defender_ai
                audio_fx_enabled = snap.audio_fx
                banner_text = snap.banner_text

                pending_music = live_state.consume_music_change()
                if pending_music:
                    try:
                        # Check if it's a YouTube URL
                        from cmd_audio.audio_input import is_youtube_url
                        if is_youtube_url(pending_music):
                            # Generate random attack pattern for YouTube
                            current_attack_pattern = get_random_attack_pattern()
                            attack_pattern_timer = time.time()
                            logs.append(f"!{visual_t:06.2f}s YouTube    ATTACK     {current_attack_pattern['type']} (intensity: {current_attack_pattern['intensity']:.2f})")
                        
                        switch_music_file(pending_music)
                    except Exception as exc:
                        live_state.set_music_status(f"Load failed: {exc}")

            key = raw.read_key()
            if key == "q":
                break
            if key == "p":
                paused = not paused
                if live_state is not None:
                    live_state.set_paused(paused)
            if key == "+":
                sensitivity = min(4.0, sensitivity + 0.05)
                if live_state is not None:
                    live_state.set_sensitivity(sensitivity)
            if key == "-":
                sensitivity = max(0.1, sensitivity - 0.05)
                if live_state is not None:
                    live_state.set_sensitivity(sensitivity)
            if key == "]":
                args.speed_max = min(6.0, args.speed_max + 0.1)
                if live_state is not None:
                    live_state.set_speed_bounds(args.speed_min, args.speed_max)
            if key == "[":
                args.speed_max = max(args.speed_min + 0.1, args.speed_max - 0.1)
                if live_state is not None:
                    live_state.set_speed_bounds(args.speed_min, args.speed_max)
            if key == "t":
                idx_theme = theme_order.index(theme_name)
                theme_name = apply_theme(theme_order[(idx_theme + 1) % len(theme_order)])
                if live_state is not None:
                    live_state.set_theme(theme_name)
            if key == "b":
                show_banner = not show_banner
                if live_state is not None:
                    live_state.set_show_banner(show_banner)
            if key == "e":
                banner_text = prompt_banner_text(raw, banner_text)
                if live_state is not None:
                    live_state.set_banner_text(banner_text)
            if key == "c":
                align_modes = ["left", "center", "right"]
                current_idx = align_modes.index(banner_align) if banner_align in align_modes else 1
                banner_align = align_modes[(current_idx + 1) % len(align_modes)]
                if live_state is not None:
                    live_state.set_banner_align(banner_align)
            if key == "v":
                anim_modes = ["off", "scroll", "pulse"]
                anim_idx = anim_modes.index(banner_anim) if banner_anim in anim_modes else 0
                banner_anim = anim_modes[(anim_idx + 1) % len(anim_modes)]
                if live_state is not None:
                    live_state.set_banner_anim(banner_anim)
            if key == "x":
                size_modes = ["normal", "large"]
                size_idx = size_modes.index(banner_size) if banner_size in size_modes else 0
                banner_size = size_modes[(size_idx + 1) % len(size_modes)]
                if live_state is not None:
                    live_state.set_banner_size(banner_size)
            if key == "m":
                other_modes = [m for m in terminal_modes if m != terminal_mode]
                terminal_mode = random.choice(other_modes) if other_modes else terminal_mode
                shell_lines = generate_shell_feed(current_level, False, terminal_mode)
                if live_state is not None:
                    live_state.set_terminal_mode(terminal_mode)
            if key == "r":
                target_lock = random.choice(TARGETS)
                operation_mode = random.choice(operation_modes)
                daemon = random.choice(["sshd", "postfix", "nginx", "xrdp", "redis"])
                shell_lines = generate_shell_feed(current_level, True, terminal_mode)
                if live_state is not None:
                    live_state.set_target_lock(target_lock)
                    live_state.set_operation_mode(operation_mode)
            if key == "z":
                start = time.perf_counter()
                visual_t = 0.0
                prev_level = 0.0
                pulse = 0
                history.clear()
                logs = [" 000.00s Boot      CONSOLE  pwr=00%", " 000.01s Route     MATRIX   pwr=00%", " 000.02s Cipher    PRIME    pwr=00%"]
                next_bpm_tick_at = bpm_interval if bpm_interval > 0 else 0.0
                target_lock = random.choice(TARGETS)
                operation_mode = random.choice(operation_modes)
                net_state = "UPLINK STABLE"
                shell_lines = generate_shell_feed(0.0, False, terminal_mode)
                mission_phase_idx = 0
                mission_phase_name = str(MISSION_PHASES[0]["name"])
                mission_objective = str(MISSION_PHASES[0]["objective"])
                defender_state = "stable"
                defender_pressure = 1.0
                glitch_frames = 0
                scanline_flash = 0
                jitter = 0
                visual_state.last_refresh = 0.0
                if player and player.poll() is None:
                    player.terminate()
                    player = launch_player(playback_input) if args.play and playback_input else None
            if key == "0":
                sensitivity = 1.0
                args.speed_min = 0.25
                args.speed_max = 3.0
                if live_state is not None:
                    live_state.set_sensitivity(sensitivity)
                    live_state.set_speed_bounds(args.speed_min, args.speed_max)
            if key == "n":
                advance_playlist(1)
            if key == "u":
                advance_playlist(-1)
            if key == "1":
                mission_timeline_enabled = not mission_timeline_enabled
                if not mission_timeline_enabled:
                    mission_phase_name = "MANUAL"
                    mission_objective = "timeline disabled"
                logs.append(f"!{visual_t:06.2f}s Toggle    mission_timeline={'on' if mission_timeline_enabled else 'off'}")
                if live_state is not None:
                    live_state.set_mission_timeline(mission_timeline_enabled)
            if key == "2":
                defender_ai_enabled = not defender_ai_enabled
                defender_state = "stable" if defender_ai_enabled else "disabled"
                logs.append(f"!{visual_t:06.2f}s Toggle    defender_ai={'on' if defender_ai_enabled else 'off'}")
                if live_state is not None:
                    live_state.set_defender_ai(defender_ai_enabled)
            if key == "3":
                audio_fx_enabled = not audio_fx_enabled
                if not audio_fx_enabled:
                    glitch_frames = 0
                    scanline_flash = 0
                    jitter = 0
                logs.append(f"!{visual_t:06.2f}s Toggle    audio_fx={'on' if audio_fx_enabled else 'off'}")
                if live_state is not None:
                    live_state.set_audio_fx(audio_fx_enabled)
            if key == "a":
                alert_tones_enabled = not alert_tones_enabled
                logs.append(f"!{visual_t:06.2f}s Toggle    alert_tones={'on' if alert_tones_enabled else 'off'}")
                if live_state is not None:
                    live_state.set_alert_tones(alert_tones_enabled)
            if key == "y":
                sync_modes = ["adaptive", "bpm", "hybrid"]
                idx_sync = sync_modes.index(args.scene_sync) if args.scene_sync in sync_modes else 0
                args.scene_sync = sync_modes[(idx_sync + 1) % len(sync_modes)]
                if live_state is not None:
                    live_state.set_scene_sync(args.scene_sync)
            if key == "k":
                q_modes = ["auto", "off"]
                idx_q = q_modes.index(args.quality_mode) if args.quality_mode in q_modes else 0
                args.quality_mode = q_modes[(idx_q + 1) % len(q_modes)]
                if live_state is not None:
                    live_state.set_quality_mode(args.quality_mode)
            if key == "j":
                args.ui_style = "minimal" if args.ui_style == "full" else "full"
                if live_state is not None:
                    live_state.set_ui_style(args.ui_style)
            if key == "g":
                set_bar_mode(not _cfg.USE_UNICODE_BARS)
                if live_state is not None:
                    live_state.set_unicode_bars(_cfg.USE_UNICODE_BARS)
            if key == "h":
                lock_scene = not lock_scene
                if live_state is not None:
                    live_state.set_lock_scene(lock_scene)
            if key == "o":
                idx_op = operation_modes.index(operation_mode) if operation_mode in operation_modes else 0
                operation_mode = operation_modes[(idx_op + 1) % len(operation_modes)]
                if live_state is not None:
                    live_state.set_operation_mode(operation_mode)
            if key == "l":
                idx_tg = TARGETS.index(target_lock) if target_lock in TARGETS else 0
                target_lock = TARGETS[(idx_tg + 1) % len(TARGETS)]
                if live_state is not None:
                    live_state.set_target_lock(target_lock)
            if key == "w":
                # Manual visual module cycling
                visual_module_cycle_idx += 1
                active_visual_modules = get_visual_modules_for_cycle(visual_module_cycle_idx)
                logs.append(f"!{visual_t:06.2f}s Visual    CYCLE      modules: {', '.join(active_visual_modules)}")
            if key == "d":
                # Toggle bass mode on/off
                if theme_mode == "manual":
                    theme_mode = "bass"
                else:
                    theme_mode = "manual"
                set_theme_mode(theme_mode)
                logs.append(f"!{visual_t:06.2f}s Theme     MODE       {theme_mode}")
                if live_state is not None:
                    live_state.set_theme_mode(theme_mode)
            if key == "D":
                # Cycle backward through themes
                idx_theme = theme_order.index(theme_name)
                theme_name = apply_theme(theme_order[(idx_theme - 1) % len(theme_order)])
                if live_state is not None:
                    live_state.set_theme(theme_name)
                logs.append(f"!{visual_t:06.2f}s Theme     BACKWARD   {theme_name}")

            if visual_t >= next_terminal_switch_at and not lock_scene:
                other_modes = [m for m in terminal_modes if m != terminal_mode]
                terminal_mode = random.choice(other_modes) if other_modes else terminal_mode
                next_terminal_switch_at = visual_t + random.uniform(args.terminal_switch_min, args.terminal_switch_max)
                shell_lines = generate_shell_feed(current_level, False, terminal_mode)

            if paused:
                if live_state is not None:
                    live_state.set_frame_drops(dropped_frames)
                time.sleep(frame_time)
                continue

            elapsed = time.perf_counter() - start
            idx = min(int(elapsed * args.fps), len(audio.levels) - 1)
            base_level = audio.levels[idx]
            level = clamp(base_level * sensitivity, 0.0, 1.0)
            current_level = level
            bands = audio.bands[idx] if idx < len(audio.bands) else [level] * 8
            beat = audio.beats[idx] if idx < len(audio.beats) else False
            flux = audio.fluxes[idx] if idx < len(audio.fluxes) else 0.0
            progress = clamp((idx * frame_time) / max(0.001, audio.duration), 0.0, 1.0)
            mission = mission_timeline_from_progress(progress)

            if mission_timeline_enabled and mission.phase_idx != mission_phase_idx:
                mission_phase_idx = mission.phase_idx
                mission_phase_name = mission.phase_name
                mission_objective = mission.objective
                defender_pressure = 1.0 + (0.35 * mission.phase_idx)
                logs.append(f"!{visual_t:06.2f}s Mission   {mission.phase_name:<8} obj={mission.objective[:28]}")
                operation_mode = mission.operation
                clearance = mission.clearance
                net_state = mission.net_state
                shell_lines = generate_shell_feed(level, True, terminal_mode)
                if alert_tones_enabled and visual_t >= tone_cooldown_until:
                    sys.stdout.write("\a")
                    tone_cooldown_until = visual_t + 0.35
                if plugin_module is not None and hasattr(plugin_module, "on_event"):
                    try:
                        plugin_module.on_event({"type": "mission_phase_change", "phase": mission.phase_name, "objective": mission.objective, "t": visual_t})
                    except Exception:
                        pass
            elif not mission_timeline_enabled:
                mission_phase_name = "MANUAL"
                mission_objective = "timeline disabled"

            bass = sum(bands[:2]) / max(1, len(bands[:2]))
            mids = sum(bands[2:5]) / max(1, len(bands[2:5]))
            highs = sum(bands[5:]) / max(1, len(bands[5:]))

            # --- Bass-reactive theme switching ---
            if theme_mode == "bass":
                bass_history.append(bass)
                if len(bass_history) > 30:
                    bass_history = bass_history[-30:]
                bass_avg = sum(bass_history) / max(1, len(bass_history))
                hard_bass = (bass > bass_avg * 1.6 + _cfg.BASS_THRESHOLD) and (level > 0.4)
                if hard_bass and (visual_t - last_bass_switch_at) > BASS_COOLDOWN:
                    idx_theme = theme_order.index(theme_name)
                    theme_name = apply_theme(theme_order[(idx_theme + 1) % len(theme_order)])
                    last_bass_switch_at = visual_t
                    logs.append(f"!{visual_t:06.2f}s Bass      SWITCH     theme={theme_name}  bass={bass:.3f}  avg={bass_avg:.3f}")
                    if live_state is not None:
                        live_state.set_theme(theme_name)
            module_levels = {
                "nodes": clamp(((0.40 * level) + (0.95 * mids)) * scene_pack_weights["nodes"], 0.0, 1.0),
                "files": clamp(((0.50 * level) + (0.25 * mids) + (0.25 * highs)) * scene_pack_weights["files"], 0.0, 1.0),
                "firewall": clamp(((0.35 * level) + (1.00 * bass)) * scene_pack_weights["firewall"], 0.0, 1.0),
                "ports": clamp(((0.30 * level) + (0.85 * bass)) * scene_pack_weights["ports"], 0.0, 1.0),
                "crypto": clamp(((0.30 * level) + (1.00 * highs)) * scene_pack_weights["crypto"], 0.0, 1.0),
                "admin": clamp(((0.45 * level) + (0.70 * highs)) * scene_pack_weights["admin"], 0.0, 1.0),
                "processes": clamp(((0.50 * level) + (0.60 * mids) + (0.20 * bass)) * scene_pack_weights["processes"], 0.0, 1.0),
                "traffic": clamp(((0.35 * level) + (0.80 * bass) + (0.30 * mids)) * scene_pack_weights["traffic"], 0.0, 1.0),
                "syslog": clamp(((0.55 * level) + (0.40 * highs) + (0.25 * mids)) * scene_pack_weights["syslog"], 0.0, 1.0),
                "filesystem": clamp(((0.40 * level) + (0.50 * mids)) * scene_pack_weights["filesystem"], 0.0, 1.0),
                "ssh-brute": clamp(((0.60 * level) + (0.50 * bass)) * scene_pack_weights["ssh-brute"], 0.0, 1.0),
                "dns": clamp(((0.30 * level) + (0.70 * highs) + (0.30 * mids)) * scene_pack_weights["dns"], 0.0, 1.0),
                "db-dump": clamp(((0.45 * level) + (0.55 * mids) + (0.25 * highs)) * scene_pack_weights["db-dump"], 0.0, 1.0),
                "memory": clamp(((0.35 * level) + (0.90 * highs) + (0.20 * bass)) * scene_pack_weights["memory"], 0.0, 1.0),
            }

            transient = abs(level - prev_level)
            speed_factor = 0.30 + (1.55 * level) + (2.2 * transient) + (1.8 * flux) + (0.75 if beat else 0.0)
            speed_factor = clamp(speed_factor, args.speed_min, args.speed_max)
            visual_t += frame_time * speed_factor
            prev_level = level

            bpm_phase_hit = False
            if bpm_interval > 0.0 and visual_t >= next_bpm_tick_at:
                bpm_phase_hit = True
                while visual_t >= next_bpm_tick_at:
                    next_bpm_tick_at += bpm_interval

            term = shutil.get_terminal_size(fallback=(100, 30))
            width = max(30, term.columns)
            height = max(10, term.lines - 1)

            hist_budget += speed_factor * 0.85
            while hist_budget >= 1.0:
                history.append(level)
                hist_budget -= 1.0
            if len(history) > 120:
                del history[: len(history) - 120]

            if beat:
                pulse = max(pulse, 5)
            if pulse > 0:
                pulse -= 1

            if audio_fx_enabled:
                if beat or flux > 0.72:
                    glitch_frames = max(glitch_frames, 2)
                    scanline_flash = max(scanline_flash, 2)
                    jitter = random.choice([0, 1])
                else:
                    glitch_frames = max(0, glitch_frames - 1)
                    scanline_flash = max(0, scanline_flash - 1)
                    if random.random() < 0.25:
                        jitter = 0
                
                # Apply YouTube attack pattern effects
                if current_attack_pattern and time.time() - attack_pattern_timer < current_attack_pattern['duration']:
                    pattern = current_attack_pattern
                    if pattern['type'] == 'glitch_effect':
                        if random.random() < pattern['params']['frequency']:
                            glitch_frames = max(glitch_frames, 3)
                            jitter = 1
                    elif pattern['type'] == 'scanline_flash':
                        if random.random() < 0.3:
                            scanline_flash = max(scanline_flash, 2)
                    elif pattern['type'] == 'signal_interference':
                        if random.random() < 0.2:
                            jitter = 1
                            glitch_frames = max(glitch_frames, 1)
                elif current_attack_pattern:
                    # Attack pattern expired
                    current_attack_pattern = None
            else:
                glitch_frames = 0
                scanline_flash = 0
                jitter = 0

            if (not lock_scene) and should_shift_scene(args.scene_sync, beat, flux, visual_t, next_scene_shift_at, bpm_phase_hit):
                target_lock = random.choice(TARGETS)
                operation_mode = mission.operation if (mission_timeline_enabled and random.random() < 0.7) else random.choice(operation_modes)
                daemon = random.choice(["sshd", "postfix", "nginx", "xrdp", "redis"])
                clearance = mission.clearance if (mission_timeline_enabled and random.random() < 0.7) else random.choice(["L1", "L2", "L3", "ROOT"] if (beat or flux > 0.72) else ["L0", "L1", "L2"])
                open_ports = random.randint(2, 16)
                trace_hops = random.randint(3, 12)
                packet = random.randint(1200, 9000)
                net_state = mission.net_state if (mission_timeline_enabled and random.random() < 0.75) else ("FIREWALL COLLAPSE" if (beat or flux > 0.72) else "UPLINK STABLE")
                next_scene_shift_at = visual_t + random.uniform(1.0, 3.5)

            # Auto-switch visual modules based on audio level/beat/time
            if visual_t >= next_visual_module_switch_at and not lock_scene:
                visual_module_cycle_idx += 1
                active_visual_modules = get_visual_modules_for_cycle(visual_module_cycle_idx)
                next_visual_module_switch_at = visual_t + random.uniform(3.0, 8.0)
                # Also switch on beat with high flux
                if beat and flux > 0.6:
                    visual_module_cycle_idx += 1
                    active_visual_modules = get_visual_modules_for_cycle(visual_module_cycle_idx)

            if beat or flux > 0.45 or visual_t >= next_shell_refresh_at:
                shell_lines = generate_shell_feed(level, beat, terminal_mode)
                next_shell_refresh_at = visual_t + random.uniform(0.45, 1.6)

            if defender_ai_enabled:
                updated_target, reroute_hops, new_defender_state, defense_action, defense_events = maybe_apply_defender_countermeasure(
                    level=level, beat=beat, flux=flux, target_lock=target_lock,
                    terminal_mode=terminal_mode, defender_pressure=defender_pressure,
                )
                if defense_action:
                    defender_state = new_defender_state
                    if updated_target != target_lock:
                        target_lock = updated_target
                    trace_hops = int(clamp(trace_hops + reroute_hops, 1, 24))
                    net_state = "COUNTERMEASURE PRESSURE"
                    logs.append(f"!{visual_t:06.2f}s Defend    {defense_action:<12} pwr={int(level*100):02d}%")
                    for ev in defense_events[:2]:
                        shell_lines.append(ev)
                    shell_lines = shell_lines[-6:]
                    if alert_tones_enabled and visual_t >= tone_cooldown_until:
                        sys.stdout.write("\a")
                        tone_cooldown_until = visual_t + 0.25
                    if plugin_module is not None and hasattr(plugin_module, "on_event"):
                        try:
                            plugin_module.on_event({"type": "defense_action", "action": defense_action, "target": target_lock, "t": visual_t})
                        except Exception:
                            pass
                elif defender_state != "stable" and random.random() < 0.05:
                    defender_state = "stable"
            else:
                defender_state = "disabled"

            if alert_tones_enabled and beat and flux > 0.70 and visual_t >= tone_cooldown_until:
                sys.stdout.write("\a")
                tone_cooldown_until = visual_t + 0.2

            refresh_visual_state(visual_state, module_levels, beat, flux, visual_t)

            # Update logs budget
            log_budget += (0.30 + (0.75 * level)) * speed_factor
            pushed = 0
            while log_budget >= 1.0 and pushed < 4:
                if random.random() < 0.65:
                    logs.append(make_incident_line(level, visual_t, beat, incident_feed))
                else:
                    logs.append(make_log_line(level, visual_t, beat))
                log_budget -= 1.0
                pushed += 1
            max_log_items = max(12, int(height * (0.55 if args.quality_mode == "auto" and dropped_frames > 120 else 1.0)))
            if len(logs) > max_log_items:
                del logs[: len(logs) - max_log_items]

            quality_scale = 0.55 if (args.quality_mode == "auto" and dropped_frames > 220) else 0.70 if (args.quality_mode == "auto" and dropped_frames > 120) else 0.85 if (args.quality_mode == "auto" and dropped_frames > 50) else 1.0

            if plugin_module is not None and hasattr(plugin_module, "on_frame_context"):
                try:
                    context_update = plugin_module.on_frame_context({
                        "level": level, "flux": flux, "beat": beat,
                        "mission_phase": mission_phase_name, "mission_objective": mission_objective,
                        "defender_state": defender_state, "module_levels": dict(module_levels),
                        "target_lock": target_lock, "operation_mode": operation_mode,
                    })
                    if isinstance(context_update, dict):
                        updated_levels = context_update.get("module_levels")
                        if isinstance(updated_levels, dict):
                            for mk in module_levels:
                                v = updated_levels.get(mk)
                                if isinstance(v, (float, int)):
                                    module_levels[mk] = clamp(float(v), 0.0, 1.0)
                        op = context_update.get("operation_mode")
                        if isinstance(op, str) and op in OPERATION_MODES:
                            operation_mode = op
                        tgt = context_update.get("target_lock")
                        if isinstance(tgt, str) and tgt in TARGETS:
                            target_lock = tgt
                except Exception:
                    pass

            audio_t = idx * frame_time

            # Render frame
            body_h = max(6, height - 4)
            if show_banner or banner_text.strip():
                banner_row_count = 5 if banner_size == "large" else 1
                body_h = max(6, body_h - banner_row_count)

            left_w = max(24, width // 3)
            right_w = max(24, width // 4)
            center_w = max(24, width - left_w - right_w - 2)

            nodes, firewall, ports_arr, crypto = render_paneled_visuals(
                level, pulse > 0, bands, history, shell_lines,
                center_w - 2, max(2, (body_h - 2) // 4), quality_scale, module_levels, visual_state,
                active_modules=active_visual_modules,
            )
            center_lines = compose_center_panel(center_w - 2, body_h - 2, nodes, firewall, ports_arr, crypto, module_names=active_visual_modules)

            left_lines = logs[-(body_h - 2):]
            right_lines = build_telemetry_lines(
                level, audio_t, audio.duration, right_w - 2, pulse, speed_factor, sensitivity,
                theme_name, terminal_mode, args.terminal_switch_min, args.terminal_switch_max,
                daemon, clearance, open_ports, trace_hops, packet, flux,
                mission_phase_name, mission_objective, defender_state, keys_line,
            )

            rows: List[str] = []
            # Extract music name for display
            music_display_name = os.path.basename(audio_path) if audio_path and audio_path != "(demo mode)" else "DEMO"
            header = f"{_cfg.GREEN_BRIGHT}CMD-AUDIO :: MUSIC SYNC CONSOLE :: {operation_mode}{_cfg.RESET}"
            beat_word = f"{_cfg.GREEN_BRIGHT}BEAT{_cfg.RESET}" if pulse > 0 else f"{_cfg.GREEN_DARK}IDLE{_cfg.RESET}"
            top_rule = f"{_cfg.GREEN_DIM}{'=' * max(1, width)}{_cfg.RESET}"
            mode_tag = "MIN" if args.ui_style == "minimal" else "FULL"
            head_line = fit_text(
                f"{header}   {beat_word}   lock:{target_lock}   mission:{mission_phase_name}   theme:{theme_name}({theme_mode})   term:{terminal_mode}   ui:{mode_tag}",
                width,
            )
            music_line = fit_text(
                f"{_cfg.GREEN_DIM}♪ Now Playing: {_cfg.GREEN_BRIGHT}{music_display_name}{_cfg.RESET}",
                width,
            )
            rows.extend([top_rule, head_line, music_line])

            if show_banner or banner_text.strip():
                for bl in build_banner_lines(banner_text, width, banner_align, banner_anim, banner_size, audio_t, pulse):
                    rows.append(f"{_cfg.GREEN_BRIGHT}{bl}{_cfg.RESET}")

            if args.ui_style == "minimal" or width < 100:
                p1_h = max(4, body_h // 3)
                p2_h = max(4, body_h // 3)
                p3_h = max(4, body_h - p1_h - p2_h)
                box1 = panel_box("events", width, p1_h, left_lines)
                mini_center = center_lines[: max(1, p2_h - 2)]
                box2 = panel_box("array", width, p2_h, mini_center)
                box3 = panel_box("telemetry", width, p3_h, right_lines)
                rows.extend(box1)
                rows.extend(box2)
                rows.extend(box3)
            elif width < 150:
                col_w_left = max(28, (width // 2) - 1)
                col_w_right = max(28, width - col_w_left - 1)
                left_box = panel_box("events", col_w_left, body_h, left_lines)
                right_body = center_lines[: max(1, (body_h - 2) // 2)] + [""] + right_lines
                right_box = panel_box("array+telemetry", col_w_right, body_h, right_body)
                for i in range(body_h):
                    rows.append(f"{left_box[i]} {right_box[i]}")
            else:
                left_box = panel_box("events", left_w, body_h, left_lines)
                center_box = panel_box("hacknet-array", center_w, body_h, center_lines)
                right_box = panel_box("telemetry", right_w, body_h, right_lines)
                for i in range(body_h):
                    rows.append(f"{left_box[i]} {center_box[i]} {right_box[i]}")

            pulse_word = random.choice(["ACCESS", "OVERRIDE", "BYPASS", "DECRYPT", "INJECT", "TRACE"]) if pulse > 0 else "SYNC"
            footer_meter_w = max(10, width - 44)
            from cmd_audio.utils import colorize_status
            footer_net = colorize_status(net_state, 0.92 if "COLLAPSE" in net_state else 0.20)
            footer = fit_text(
                f"{_cfg.GREEN_BRIGHT}::{pulse_word:<8}::{_cfg.RESET} {meter_bar(level, footer_meter_w)}  flux:{int(flux * 100):3d}%  {footer_net}",
                width,
            )
            rows.append(footer)
            rows.append(top_rule)
            rows = apply_terminal_fx(rows, width, glitch_frames, scanline_flash, jitter)
            # Pad rows to exactly height lines to prevent vertical shift
            while len(rows) < height:
                rows.append(" " * width)
            rows = rows[:height]
            frame = "\n".join(rows)

            sys.stdout.write("\033[H")
            sys.stdout.write(frame)
            sys.stdout.write("\033[J")
            sys.stdout.flush()

            if args.ui and live_state is not None and not ui_started:
                live_ui = start_live_control_window(live_state)
                ui_started = True

            if rec is not None:
                write_record_frame(rec, args.record_mode, visual_t, speed_factor, frame)

            if idx >= len(audio.levels) - 1:
                if not advance_playlist(1):
                    break
                continue

            target = start + (idx + 1) * frame_time
            sleep_for = target - time.perf_counter()
            if sleep_for > 0:
                time.sleep(sleep_for)
            else:
                late_frames = max(1, int((-sleep_for) / frame_time))
                dropped_frames += late_frames

            if live_state is not None:
                live_state.set_frame_drops(dropped_frames)

    finally:
        raw.disable()
        sys.stdout.write(_cfg.SHOW_CURSOR + _cfg.RESET + "\n")
        sys.stdout.flush()
        if rec is not None:
            rec.close()
        if args.video_hook and args.record_file:
            env = os.environ.copy()
            env["CMD_AUDIO_RECORD_FILE"] = args.record_file
            try:
                subprocess.run(args.video_hook, shell=True, env=env, check=False)
            except Exception as exc:
                logger.error("Video hook error: %s", exc)
        if player and player.poll() is None:
            player.terminate()
        if cleanup_wav:
            try:
                os.unlink(wav_input)
            except OSError:
                pass
        if web_server is not None:
            try:
                web_server.stop()
            except Exception:
                pass
        if remote_sock is not None:
            try:
                remote_sock.stop()
            except Exception:
                pass
        close_live_ui()

    return 0