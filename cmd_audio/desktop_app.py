"""Desktop app wrapper (Phase 5.8)."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


def check_electron_available() -> bool:
    """Check if Electron is available."""
    try:
        result = subprocess.run(["electron", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_tauri_available() -> bool:
    """Check if Tauri is available."""
    try:
        result = subprocess.run(["cargo", "tauri", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def create_electron_package() -> bool:
    """Create Electron desktop app."""
    pkg_dir = os.path.join(os.path.dirname(__file__), "..", "electron-app")
    if not os.path.isdir(pkg_dir):
        os.makedirs(pkg_dir, exist_ok=True)
    pkg_json = os.path.join(pkg_dir, "package.json")
    if not os.path.exists(pkg_json):
        import json
        with open(pkg_json, "w") as f:
            json.dump({
                "name": "cmd-audio-desktop",
                "version": "0.1.0",
                "main": "main.js",
                "dependencies": {"electron": "^25.0.0"},
            }, f, indent=2)
    logger.info("Electron package created at %s", pkg_dir)
    return True


def launch_electron() -> bool:
    pkg_dir = os.path.join(os.path.dirname(__file__), "..", "electron-app")
    if not os.path.isdir(pkg_dir):
        return False
    try:
        subprocess.run(["npm", "start"], cwd=pkg_dir, check=True)
        return True
    except Exception as e:
        logger.error("Failed to launch Electron: %s", e)
        return False