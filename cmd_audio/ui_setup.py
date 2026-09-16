"""Pre-run setup UI — HTML settings page served via web server (replaces tkinter popup)."""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
import threading
from typing import Any, Dict, Optional

from cmd_audio.logging_config import get_logger
from cmd_audio.web_server import AudioServer

__all__ = ["setup_run_with_ui"]

logger = get_logger(__name__)


def _apply_args_from_config(args: argparse.Namespace, config: Dict[str, Any]) -> None:
    """Apply a dict of config values to the argparse Namespace."""
    from cmd_audio.config import THEMES, PRESETS

    # String fields
    for field in ("audio", "source", "youtube", "playlist", "scene_sync", "quality_mode",
                   "ui_style", "theme", "theme_mode", "preset", "banner_text", "banner_align",
                   "banner_anim", "banner_size", "record_file", "record_mode",
                   "plugin", "video_hook", "scene_pack", "scene_pack_file", "mqtt", "osc"):
        val = config.get(field)
        if val is not None and field == "audio":
            # audio comes as a string from the form
            if isinstance(val, str) and val.strip():
                args.audio = [val.strip()]
            elif isinstance(val, list):
                args.audio = val
        elif val is not None:
            setattr(args, field, val)

    # Integer fields
    for field in ("capture_seconds", "fps"):
        val = config.get(field)
        if val is not None:
            try:
                setattr(args, field, int(val))
            except (ValueError, TypeError):
                pass

    # Float fields
    for field in ("sensitivity", "speed_min", "speed_max",
                   "terminal_switch_min", "terminal_switch_max", "bass_threshold"):
        val = config.get(field)
        if val is not None:
            try:
                setattr(args, field, float(val))
            except (ValueError, TypeError):
                pass

    # Seed (can be null)
    seed_val = config.get("seed")
    if seed_val is not None:
        try:
            args.seed = int(seed_val)
        except (ValueError, TypeError):
            args.seed = None

    # Boolean fields
    for field in ("play", "show_banner", "keep_converted", "alert_tones",
                   "mission_timeline", "defender_ai", "audio_fx", "diagnostics",
                   "normalize", "profile", "adaptive_fps", "high_contrast",
                   "detect_player", "theme_transition", "web", "rest_api",
                   "network_trigger", "chat", "ai_scenes", "gpu", "collab",
                   "remote_control", "unicode_bars"):
        val = config.get(field)
        if val is not None:
            setattr(args, field, bool(val))


def _build_config_dict(args: argparse.Namespace) -> Dict[str, Any]:
    """Build a config dict from current args for pre-populating the form."""
    audio_list = getattr(args, "audio", [])
    audio_str = " ".join(audio_list).strip() if isinstance(audio_list, list) else str(audio_list)
    return {
        "audio": audio_str,
        "source": getattr(args, "source", "file"),
        "youtube": getattr(args, "youtube", ""),
        "playlist": getattr(args, "playlist", ""),
        "capture_seconds": getattr(args, "capture_seconds", 30),
        "fps": getattr(args, "fps", 30),
        "play": getattr(args, "play", True),
        "sensitivity": getattr(args, "sensitivity", 1.0),
        "speed_min": getattr(args, "speed_min", 0.25),
        "speed_max": getattr(args, "speed_max", 3.0),
        "terminal_switch_min": getattr(args, "terminal_switch_min", 4.0),
        "terminal_switch_max": getattr(args, "terminal_switch_max", 11.0),
        "seed": getattr(args, "seed", None),
        "theme": getattr(args, "theme", "matrix"),
        "theme_mode": getattr(args, "theme_mode", "manual"),
        "bass_threshold": getattr(args, "bass_threshold", 0.15),
        "preset": getattr(args, "preset", ""),
        "scene_sync": getattr(args, "scene_sync", "adaptive"),
        "quality_mode": getattr(args, "quality_mode", "auto"),
        "banner_text": getattr(args, "banner_text", ""),
        "banner_align": getattr(args, "banner_align", "center"),
        "banner_anim": getattr(args, "banner_anim", "off"),
        "banner_size": getattr(args, "banner_size", "normal"),
        "show_banner": getattr(args, "show_banner", False),
        "keep_converted": getattr(args, "keep_converted", False),
        "alert_tones": getattr(args, "alert_tones", False),
        "mission_timeline": getattr(args, "mission_timeline", True),
        "defender_ai": getattr(args, "defender_ai", True),
        "audio_fx": getattr(args, "audio_fx", True),
        "diagnostics": getattr(args, "diagnostics", False),
        "record_file": getattr(args, "record_file", ""),
        "record_mode": getattr(args, "record_mode", "jsonl"),
        "plugin": getattr(args, "plugin", ""),
        "video_hook": getattr(args, "video_hook", ""),
        "scene_pack": getattr(args, "scene_pack", ""),
        "scene_pack_file": getattr(args, "scene_pack_file", ""),
        "normalize": getattr(args, "normalize", False),
        "profile": getattr(args, "profile", False),
        "adaptive_fps": getattr(args, "adaptive_fps", False),
        "high_contrast": getattr(args, "high_contrast", False),
        "detect_player": getattr(args, "detect_player", False),
        "theme_transition": getattr(args, "theme_transition", False),
        "mqtt": getattr(args, "mqtt", ""),
        "osc": getattr(args, "osc", ""),
        "web": getattr(args, "web", False),
        "rest_api": getattr(args, "rest_api", False),
        "network_trigger": getattr(args, "network_trigger", False),
        "chat": getattr(args, "chat", False),
        "ai_scenes": getattr(args, "ai_scenes", False),
        "gpu": getattr(args, "gpu", False),
        "collab": getattr(args, "collab", False),
        "remote_control": getattr(args, "remote_control", False),
        "unicode_bars": getattr(args, "unicode_bars", False),
    }


def setup_run_with_ui(args: argparse.Namespace) -> Optional[AudioServer]:
    """Start a web server with an HTML settings page; blocks until user submits or cancels.

    Returns the AudioServer on success (kept running for live controls), None if cancelled.
    """
    from cmd_audio.web_server import AudioServer

    host = "localhost"
    port = 8080
    server = AudioServer(host=host, port=port)

    # Pre-populate the form with current args
    server.set_current_config(_build_config_dict(args))

    # Load live controls HTML from disk
    import os
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "live_controls.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            server.set_live_controls_html(f.read())
        logger.info("Loaded live controls HTML from %s", html_path)
    else:
        logger.warning("live_controls.html not found at %s", html_path)

    try:
        server.start()
    except Exception as exc:
        logger.error("Failed to start setup web server: %s", exc)
        return None

    url = f"http://{host}:{port}"
    print(f"\n  CMD-AUDIO Setup UI: {url}\n")
    print(f"  Open the URL above in your browser to configure settings.\n")
    print(f"  Press Ctrl+C in this terminal to cancel.\n")

    # Try to open browser automatically
    try:
        webbrowser.open(url)
    except Exception:
        pass

    # Block until user submits the form or cancels
    config = server.wait_for_config(timeout=600.0)

    if config is None:
        logger.info("Setup UI cancelled by user")
        try:
            server.stop()
        except Exception:
            pass
        return None

    # Apply the received config to args
    try:
        _apply_args_from_config(args, config)
        logger.info("Setup UI: config applied successfully")
        # Keep server running for live controls during render loop
        return server
    except Exception as exc:
        logger.error("Failed to apply config from UI: %s", exc)
        try:
            server.stop()
        except Exception:
            pass
        return None