"""CLI help documentation and man-page generation (Phase 1.7)."""

from __future__ import annotations

import argparse
import os
import sys
from typing import List
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with grouped sections."""
    parser = argparse.ArgumentParser(
        prog="cmd-audio",
        description="Music-reactive terminal hacker visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  cmd-audio music.mp3\n"
            "  cmd-audio --theme cyberpunk music.mp3\n"
            "  cmd-audio --fps 60 --sensitivity 2.0 music.mp3\n"
            "  cmd-audio --demo\n"
            "  cmd-audio --page music.mp3 --record out.jsonl\n"
            "\n"
            "Keys:\n"
            "  q=quit p=pause t=cycle-theme +/- adjust-sensitivity\n"
            "  </> speed-adjust n=next v=cycle-visual-help\n"
        ),
    )

    # Audio source group
    parser.add_argument("audio", nargs="?", default="", help="Audio file path (mp3, wav, etc.) or YouTube URL")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode with synthetic audio")
    parser.add_argument("--fps", type=int, default=30, help="Target frames per second (1-120)")
    parser.add_argument("--sensitivity", type=float, default=1.0, help="Audio sensitivity (0.0-5.0)")
    parser.add_argument("--theme", default="matrix", help="Color theme (matrix, cyberpunk, neon, etc.)")
    parser.add_argument("--theme-mode", default="manual", choices=["manual", "bass"], help="Theme switching mode")
    parser.add_argument("--bass-threshold", type=float, default=0.15, help="Bass threshold (0.0-1.0)")
    parser.add_argument("--banner", default="", help="Banner text (centered text overlay)")
    parser.add_argument("--banner-align", default="center", choices=["left", "center", "right"])
    parser.add_argument("--banner-anim", default="off", choices=["off", "scroll", "pulse"])
    parser.add_argument("--banner-size", default="normal", choices=["normal", "large"])
    parser.add_argument("--show-banner", action="store_true", help="Show the banner")
    parser.add_argument("--record", default="", help="Record output to file (jsonl, txt, gz)")
    parser.add_argument("--record-mode", default="jsonl", choices=["jsonl", "txt", "txt-clean", "jsonl.gz", "txt.gz", "txt-clean.gz"])
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible rendering")
    parser.add_argument("--speed-min", type=float, default=0.25, help="Minimum playback speed")
    parser.add_argument("--speed-max", type=float, default=3.0, help="Maximum playback speed")
    parser.add_argument("--terminal-switch-min", type=float, default=4.0)
    parser.add_argument("--terminal-switch-max", type=float, default=11.0)
    parser.add_argument("--ui-style", default="full", choices=["full", "minimal", "panel", "spectrogram"])
    parser.add_argument("--quality-mode", default="auto", choices=["auto", "low", "high"])
    parser.add_argument("--scene-sync", default="adaptive", choices=["adaptive", "manual", "off"])
    parser.add_argument("--plugin", default="", help="Plugin Python file path")
    parser.add_argument("--scene-pack", default="", help="Scene pack name")
    parser.add_argument("--scene-pack-file", default="", help="Scene pack JSON file")
    parser.add_argument("--mission-timeline", action="store_true")
    parser.add_argument("--no-mission-timeline", action="store_true")
    parser.add_argument("--defender-ai", action="store_true")
    parser.add_argument("--no-defender-ai", action="store_true")
    parser.add_argument("--audio-fx", action="store_true")
    parser.add_argument("--no-audio-fx", action="store_true")
    parser.add_argument("--alert-tones", action="store_true")
    parser.add_argument("--no-alert-tones", action="store_true")
    parser.add_argument("--unicode-bars", action="store_true")
    parser.add_argument("--no-unicode-bars", action="store_true")
    parser.add_argument("--profile", action="store_true", help="Enable performance profiling")
    parser.add_argument("--web", action="store_true", help="Start web server mode")
    parser.add_argument("--web-port", type=int, default=8080)
    parser.add_argument("--web-host", default="localhost")
    parser.add_argument("--stream", action="store_true", help="Stream audio from microphone")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser


def generate_man_page() -> str:
    """Generate a man page from the argparse parser."""
    parser = create_parser()
    parser.format_help()
    lines = [
        ".TH CMD-AUDIO 1 \"2024-01-01\" \"cmd-audio\" \"User Manual\"",
        ".SH NAME",
        "cmd-audio \\- Music-reactive terminal hacker visualization",
        ".SH SYNOPSIS",
        "cmd-audio [options] [audio_file]",
        ".SH DESCRIPTION",
        "A Python-based music-reactive terminal hacker visualization with 30+ visual modules,",
        "10 themes, mission system, defender AI, plugin system, and more.",
        ".SH OPTIONS",
    ]
    for action in parser._actions:
        if isinstance(action, argparse._HelpAction):
            continue
        lines.append(f".TP")
        lines.append(f"\\fB{', '.join(action.option_strings)}\\fR")
        if action.help:
            lines.append(f"{action.help}")
    return "\n".join(lines)