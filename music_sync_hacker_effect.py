#!/usr/bin/env python3
"""
Music-synced terminal hacker effect with optional popup configuration UI.

Features Hacknet-style visuals:
  - Network node topology (nodes, ports, connection status)
  - File transfer progress bars for data exfiltration
  - Firewall breach visualization with states
  - Encryption cracking progress indicators 
  - Port scan results with service detection
  - Admin detection and alert levels
    - Revamped tri-panel UI with cleaner module separators and meter bars
  Cycles through modes every 4 seconds based on music intensity.

    python3 music_sync_hacker_effect.py --config profile.json
    python3 music_sync_hacker_effect.py --preset chaos --diagnostics
    python3 music_sync_hacker_effect.py --replay-file frames.jsonl.gz

Live keys while running:
  q quit, p pause, + increase sensitivity, - decrease sensitivity,
    ] increase max speed, [ decrease max speed, t cycle theme,
    b toggle banner, e edit banner text, c cycle banner align,
    v cycle banner animation, x cycle banner size,
        m switch terminal profile, r randomize scene,
    z reset music/session, 0 reset sensitivity and speed defaults,
    n/u next/previous track,
    1/2/3 toggle mission/defender/audio-fx, a toggle alert tones,
    y scene sync, k quality mode, j ui style, g unicode bars,
    h lock scene, o operation mode, l target lock
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import math
import os
import random
import re
import select
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import termios
import threading
import time
import tty
import wave
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TextIO, Tuple

RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR = "\033[2J\033[H"

GREEN_BRIGHT = "\033[92m"
GREEN_DIM = "\033[32m"
GREEN_DARK = "\033[2;32m"
STATUS_OK = "\033[92m"
STATUS_WARN = "\033[93m"
STATUS_CRIT = "\033[91m"

ALERT_WORDS = ["ACCESS", "OVERRIDE", "BYPASS", "DECRYPT", "INJECT", "TRACE"]
LOG_ACTIONS = ["Handshake", "Route", "Cipher", "Token", "Tunnel", "Node", "Trace"]
TARGETS = ["corp-gw", "bank-node", "sat-relay", "cdn-edge", "sec-ops", "mail-spool", "black-ice"]
PORTS = ["22", "25", "53", "80", "110", "143", "443", "3389", "8080"]

HACKNET_OPERATIONS = [
    "sys_exec",
    "file_copy",
    "net_scan",
    "crack_pass",
    "port_knock",
    "exploit",
    "exfil",
    "cover_track",
    "install_trojan",
    "backdoor",
    "keylog",
    "proxy_chain",
]

FIREWALL_STATES = ["OFFLINE", "FIREWALL_ACTIVE", "ICE_DETECTED", "WALL_BREACH", "FIREWALL_DOWN"]

ADMIN_NOTICES = [
    "admin_alert: unauthorized access detected",
    "admin_notice: system intrusion on port {port}",
    "admin_alert: suspicious process spawned",
    "security: anomalous network traffic",
    "alert: privilege escalation attempt blocked",
    "warning: encryption keyspace compromised",
]

FILE_OPS = [
    "bank_vault.dat",
    "encryption.key",
    "admin_pass.txt",
    "client_data.zip",
    "security_config.xml",
    "user_db.sql",
    "source_code.tar.gz",
    "exploit_payload.bin",
]

NODE_TYPES = ["MAINFRAME", "ROUTER", "PROXY", "FIREWALL", "DATABASE", "WORKSTATION", "SERVER"]

ENCRYPTION_ALGOS = ["RSA-2048", "AES-256", "MD5-LEGACY", "SHA-512", "ECC-384", "DES-OLD"]
OPERATION_MODES = ["BREACH", "RECON", "SPOOF", "EXFIL", "BACKDOOR"]
TERMINAL_PROFILES: Dict[str, Dict[str, List[str] | str]] = {
    "netrunner": {
        "prompt": "root@localhost:~#",
        "commands": [
            "nmap -sV {host}",
            "probe --ssl {host}:443",
            "ssh root@{host}",
            "crack --wordlist top2k {host}",
            "porthack --target {host}",
            "inject --payload zero-day.bin {host}",
        ],
        "status": [
            "[+] exploit fired on {host} -- shell opened",
            "[.] brute-force window open -- retries {count}",
            "[*] bypass stage active on {host}",
        ],
    },
    "forensics": {
        "prompt": "analyst@tracebox:/evidence$",
        "commands": [
            "strings dump.mem | grep token",
            "grep -R auth_fail /var/log",
            "pcap-scan session.pcap --host {host}",
            "timeline --source /mnt/disk0",
            "sha256sum *.bin",
        ],
        "status": [
            "[*] artifact match: {host}",
            "[.] index rebuild running ({count} shards)",
            "[+] hidden marker extracted from packet stream",
        ],
    },
    "industrial": {
        "prompt": "ops@scada-node:/ctl$",
        "commands": [
            "modbus-scan --target {host}",
            "plc-dump --rack 0 --slot 2",
            "opcua-enum --host {host}",
            "safety-bypass --arm",
            "relay-map --net plant-a",
        ],
        "status": [
            "[!] pressure valve heartbeat unstable",
            "[*] actuator loop accepted spoof frame",
            "[.] watchdog delay at {count} ms",
        ],
    },
    "crypto-lab": {
        "prompt": "qx@cipher-lab:/matrix$",
        "commands": [
            "factor --modulus rsa4096.bin",
            "rainbow-lookup --hashes leak.txt",
            "decrypt --alg aes256 --keyspace full",
            "entropy-map --input payload.enc",
            "nonce-audit --stream {host}",
        ],
        "status": [
            "[+] key candidate accepted at round {count}",
            "[*] collision window around block 7",
            "[.] side-channel trace updated",
        ],
    },
    "black-ice": {
        "prompt": "intruder@icewall:/tmp$",
        "commands": [
            "mask --identity maintenance-bot",
            "ghost-route --through {host}",
            "scramble --metadata session.log",
            "wipe --sig all --path /tmp/.trace",
            "decoy-spawn --count 6",
        ],
        "status": [
            "[!] ICE wake-up timer: {count}s",
            "[*] counter-intrusion daemon sandboxed",
            "[+] trail erased from mirror nodes",
        ],
    },
    "file-exfil": {
        "prompt": "exfil@transfer:~$",
        "commands": [
            "rsync --compress --progress {host}:/secure/data.zip .",
            "scp -r root@{host}:/var/backups backup_copy",
            "wget --recursive http://{host}:8080/confidential",
            "ftp get admin_creds.txt",
            "mount -t cifs //{host}/share /mnt/smb_mount",
        ],
        "status": [
            "[*] transfer to {host}: {count}% complete",
            "[+] file exfiltration pipeline active",
            "[.] data chunk {count} encrypted and queued",
        ],
    },
    "port-scan": {
        "prompt": "scan@reconnaissance:~$",
        "commands": [
            "nmap -sS -sV -p 1-65535 {host}",
            "masscan -p1-10000 {host} --rate 10000",
            "zmap -p 443 {host}/24 -o scan_results.txt",
            "netstat -tlnp | grep LISTEN",
            "ss -tunap | grep ESTABLISHED",
        ],
        "status": [
            "[*] port scan probe {count}/100 sent",
            "[+] service identified on port {count}",
            "[.] port knock sequence verified",
        ],
    },
    "firewall-breach": {
        "prompt": "breach@firewall:~$",
        "commands": [
            "iptables -F INPUT && iptables -P INPUT DROP",
            "pf: table <block> flush",
            "firewall_down --target {host} --method exploit",
            "bypass-waf --layer 7 --payload {host}",
            "tcp-reset --source {host} --destination any",
        ],
        "status": [
            "[!] firewall state: {count}% disabled",
            "[+] breach payload executing",
            "[*] WAF rule {count} bypassed",
        ],
    },
    "encrypt-crack": {
        "prompt": "crack@cipher:~$",
        "commands": [
            "hashcat -m 1000 -a 3 hashes.txt ?a?a?a?a",
            "john --wordlist rockyou.txt --format bcrypt pass_hashes",
            "gpg --decrypt --passphrase-fd 0 vault.gpg",
            "openssl enc -aes-256-cbc -d -in data.enc",
            "cuda-accelerated bruteforce --target {host} --algo AES-256",
        ],
        "status": [
            "[.] keyspace search {count}% done",
            "[+] cipher cracked on attempt {count}",
            "[*] decryption key recovered",
        ],
    },
    "admin-hunt": {
        "prompt": "hunt@privilege_esc:~$",
        "commands": [
            "sudo -l 2>/dev/null | grep NOPASSWD",
            "find / -perm -4000 -ls 2>/dev/null | head -20",
            "getfacl /root 2>/dev/null",
            "dmesg | grep priv_esc",
            "capsh --print | grep cap_",
        ],
        "status": [
            "[*] admin account {count} located",
            "[+] privilege escalation vector found",
            "[!] root shell acquired via CVE-{count}",
        ],
    },
}
FREQ_CENTERS = [65.0, 120.0, 220.0, 440.0, 880.0, 1760.0, 3520.0, 7040.0]

THEMES: Dict[str, Tuple[str, str, str]] = {
    "matrix": ("\033[92m", "\033[32m", "\033[2;32m"),
    "red-alert": ("\033[91m", "\033[31m", "\033[2;31m"),
    "ice": ("\033[96m", "\033[36m", "\033[2;36m"),
    "amber": ("\033[93m", "\033[33m", "\033[2;33m"),
    "neon": ("\033[38;5;201m", "\033[38;5;165m", "\033[38;5;125m"),
    "plasma": ("\033[94m", "\033[34m", "\033[2;34m"),
    "ghost": ("\033[97m", "\033[37m", "\033[2;37m"),
    "magma": ("\033[91m", "\033[38;5;208m", "\033[2;31m"),
    "storm": ("\033[94m", "\033[36m", "\033[2;34m"),
    "twilight": ("\033[35m", "\033[34m", "\033[2;35m"),
}

THEME_STYLES: Dict[str, Dict[str, str]] = {
    "matrix": {
        "bright": "\033[92m",
        "dim": "\033[32m",
        "dark": "\033[2;32m",
        "bar_on": "#",
        "bar_off": " ",
        "spark": "0123456789",
    },
    "red-alert": {
        "bright": "\033[91m",
        "dim": "\033[31m",
        "dark": "\033[2;31m",
        "bar_on": "=",
        "bar_off": " ",
        "spark": "9876543210",
    },
    "ice": {
        "bright": "\033[96m",
        "dim": "\033[36m",
        "dark": "\033[2;36m",
        "bar_on": "*",
        "bar_off": " ",
        "spark": "0011223344",
    },
    "amber": {
        "bright": "\033[93m",
        "dim": "\033[33m",
        "dark": "\033[2;33m",
        "bar_on": "+",
        "bar_off": " ",
        "spark": "1234543210",
    },
    "neon": {
        "bright": "\033[38;5;201m",
        "dim": "\033[38;5;165m",
        "dark": "\033[38;5;125m",
        "bar_on": "▰",
        "bar_off": "▱",
        "spark": "⚡✧⚡✦⚡✧",
    },
    "plasma": {
        "bright": "\033[94m",
        "dim": "\033[34m",
        "dark": "\033[2;34m",
        "bar_on": "█",
        "bar_off": "░",
        "spark": "∞≈≠≈∞≈≠",
    },
    "ghost": {
        "bright": "\033[97m",
        "dim": "\033[37m",
        "dark": "\033[2;37m",
        "bar_on": "▓",
        "bar_off": "░",
        "spark": "·•′″‴",
    },
    "magma": {
        "bright": "\033[91m",
        "dim": "\033[38;5;208m",
        "dark": "\033[2;31m",
        "bar_on": "▥",
        "bar_off": "▤",
        "spark": "░▒▓██▓▒",
    },
    "storm": {
        "bright": "\033[94m",
        "dim": "\033[36m",
        "dark": "\033[2;34m",
        "bar_on": "▬",
        "bar_off": "─",
        "spark": "⚡≈⚡≈⚡",
    },
    "twilight": {
        "bright": "\033[35m",
        "dim": "\033[34m",
        "dark": "\033[2;35m",
        "bar_on": "◈",
        "bar_off": "◇",
        "spark": "★✦✧✦★",
    },
}

CURRENT_STYLE = THEME_STYLES["matrix"]
USE_UNICODE_BARS = False

DEFAULTS: Dict[str, float] = {
    "sensitivity": 1.0,
    "speed_min": 0.25,
    "speed_max": 3.0,
    "terminal_switch_min": 4.0,
    "terminal_switch_max": 11.0,
}

PRESETS: Dict[str, Dict[str, Any]] = {
    "cinematic": {
        "sensitivity": 0.9,
        "speed_min": 0.18,
        "speed_max": 2.0,
        "terminal_switch_min": 6.0,
        "terminal_switch_max": 14.0,
        "theme": "ice",
        "scene_sync": "hybrid",
    },
    "chaos": {
        "sensitivity": 1.4,
        "speed_min": 0.45,
        "speed_max": 4.5,
        "terminal_switch_min": 2.0,
        "terminal_switch_max": 6.0,
        "theme": "red-alert",
        "scene_sync": "adaptive",
    },
    "minimal": {
        "sensitivity": 0.7,
        "speed_min": 0.12,
        "speed_max": 1.4,
        "terminal_switch_min": 8.0,
        "terminal_switch_max": 18.0,
        "theme": "amber",
        "scene_sync": "bpm",
    },
}

SCENE_PACKS: Dict[str, Dict[str, Any]] = {
    "balanced": {
        "scene_sync": "adaptive",
        "quality_mode": "auto",
        "ui_style": "full",
        "module_weights": {
            "nodes": 1.0,
            "files": 1.0,
            "firewall": 1.0,
            "ports": 1.0,
            "crypto": 1.0,
            "admin": 1.0,
        },
    },
    "intrusion": {
        "scene_sync": "hybrid",
        "quality_mode": "auto",
        "ui_style": "full",
        "module_weights": {
            "nodes": 1.2,
            "files": 0.8,
            "firewall": 1.3,
            "ports": 1.25,
            "crypto": 0.9,
            "admin": 1.1,
        },
    },
    "data-heist": {
        "scene_sync": "bpm",
        "quality_mode": "auto",
        "ui_style": "minimal",
        "module_weights": {
            "nodes": 0.85,
            "files": 1.35,
            "firewall": 0.9,
            "ports": 0.95,
            "crypto": 1.2,
            "admin": 1.0,
        },
    },
}

MISSION_PHASES: List[Dict[str, Any]] = [
    {
        "name": "RECON",
        "objective": "Map perimeter hosts and establish initial foothold",
        "operation": "RECON",
        "clearance": "L0",
        "net_state": "PASSIVE SWEEP",
    },
    {
        "name": "BREACH",
        "objective": "Exploit exposed services and collapse firewall segments",
        "operation": "BREACH",
        "clearance": "L1",
        "net_state": "FIREWALL COLLAPSE",
    },
    {
        "name": "EXFIL",
        "objective": "Secure data channel and stream priority assets",
        "operation": "EXFIL",
        "clearance": "L2",
        "net_state": "EXFIL PIPELINE",
    },
    {
        "name": "CLEANUP",
        "objective": "Purge traces, rotate identities, and disengage",
        "operation": "BACKDOOR",
        "clearance": "L3",
        "net_state": "TRACE WIPE",
    },
]

DEFENDER_ACTIONS = [
    "ip-ban-wave",
    "port-rotation",
    "honeypot-lure",
    "traceback-sweep",
]


@dataclass
class AudioFeatures:
    fps: int
    duration: float
    levels: List[float]
    bands: List[List[float]]
    beats: List[bool]
    fluxes: List[float]
    beat_times: List[float]
    bpm_estimate: float


@dataclass
class VisualState:
    node_rows: List[Tuple[str, str, bool]]
    file_rows: List[str]
    firewall_state: str
    crypto_algo: str
    port_rows: List[Tuple[str, str]]
    admin_rows: List[str]
    last_refresh: float


@dataclass
class MissionTimeline:
    phase_idx: int
    phase_name: str
    objective: str
    operation: str
    clearance: str
    net_state: str


@dataclass
class IncidentFeedState:
    host: str
    phase: int
    ttl: int


class RawInput:
    def __init__(self) -> None:
        self.enabled = False
        self.fd: Optional[int] = None
        self.old = None

    def enable(self) -> None:
        if not sys.stdin.isatty() or os.name != "posix":
            return
        fd = sys.stdin.fileno()
        self.fd = fd
        self.old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        self.enabled = True

    def disable(self) -> None:
        if self.enabled and self.fd is not None and self.old is not None:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
        self.enabled = False

    def read_key(self) -> Optional[str]:
        if not self.enabled or self.fd is None:
            return None
        r, _, _ = select.select([sys.stdin], [], [], 0)
        if not r:
            return None
        ch = os.read(self.fd, 1)
        if not ch:
            return None
        return ch.decode("utf-8", errors="ignore")


def apply_theme(name: str) -> str:
    global GREEN_BRIGHT, GREEN_DIM, GREEN_DARK, CURRENT_STYLE
    if name not in THEME_STYLES:
        name = "matrix"
    CURRENT_STYLE = THEME_STYLES[name]
    GREEN_BRIGHT = CURRENT_STYLE["bright"]
    GREEN_DIM = CURRENT_STYLE["dim"]
    GREEN_DARK = CURRENT_STYLE["dark"]
    return name


def set_bar_mode(use_unicode: bool) -> None:
    global USE_UNICODE_BARS
    USE_UNICODE_BARS = bool(use_unicode)


def semantic_color(risk: float) -> str:
    if risk >= 0.75:
        return STATUS_CRIT
    if risk >= 0.45:
        return STATUS_WARN
    return STATUS_OK


def colorize_status(text: str, risk: float) -> str:
    return f"{semantic_color(risk)}{text}{RESET}"


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

    defaults = {
        "nodes": 1.0,
        "files": 1.0,
        "firewall": 1.0,
        "ports": 1.0,
        "crypto": 1.0,
        "admin": 1.0,
    }
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
    if isinstance(value, str) and value in THEME_STYLES:
        return value
    return None


def merge_args_with_config(argv: List[str], config_data: Dict[str, Any]) -> List[str]:
    # CLI flags should win over config values; only inject config flags when absent.
    out = list(argv)
    cli_text = " ".join(argv)

    if not any(not a.startswith("-") for a in argv):
        audio_val = config_data.get("audio")
        if isinstance(audio_val, str) and audio_val.strip():
            out.insert(0, audio_val.strip())

    mapping = {
        "source": "--source",
        "capture_seconds": "--capture-seconds",
        "fps": "--fps",
        "seed": "--seed",
        "sensitivity": "--sensitivity",
        "speed_min": "--speed-min",
        "speed_max": "--speed-max",
        "terminal_switch_min": "--terminal-switch-min",
        "terminal_switch_max": "--terminal-switch-max",
        "theme": "--theme",
        "banner_text": "--banner-text",
        "banner_align": "--banner-align",
        "banner_anim": "--banner-anim",
        "banner_size": "--banner-size",
        "record_file": "--record-file",
        "record_mode": "--record-mode",
        "video_hook": "--video-hook",
        "plugin": "--plugin",
        "replay_file": "--replay-file",
        "preset": "--preset",
        "scene_sync": "--scene-sync",
        "quality_mode": "--quality-mode",
        "ui_style": "--ui-style",
        "scene_pack": "--scene-pack",
        "scene_pack_file": "--scene-pack-file",
        "playlist": "--playlist",
        "alert_tones": "--alert-tones",
        "mission_timeline": "--mission-timeline",
        "defender_ai": "--defender-ai",
        "audio_fx": "--audio-fx",
        "setup_ui": "--setup-ui",
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
        "play": "--mute",
        "ui": "--no-ui",
        "mission_timeline": "--no-mission-timeline",
        "defender_ai": "--no-defender-ai",
        "audio_fx": "--no-audio-fx",
        "setup_ui": "--no-setup-ui",
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


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Music-synced terminal hacker effect")
    p.add_argument("--config", default="", help="Optional JSON config path")
    p.add_argument("--save-config", default="", help="Write current settings to JSON and exit")
    p.add_argument("audio", nargs="*", help="Audio path (supports unquoted spaces)")
    p.add_argument("--source", choices=["file", "mic", "system"], default="file")
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
    p.add_argument("--banner-text", default="", help="Optional text banner to show in the output")
    p.add_argument("--banner-align", choices=["left", "center", "right"], default="center", help="Banner text alignment")
    p.add_argument("--banner-anim", choices=["off", "scroll", "pulse"], default="off", help="Banner animation style")
    p.add_argument("--banner-size", choices=["normal", "large"], default="normal", help="Banner text size")
    p.add_argument("--show-banner", action="store_true", help="Show banner line even if banner text is empty")
    p.add_argument("--keep-converted", action="store_true", help="Keep temporary WAV conversion")
    p.add_argument("--record-file", default="", help="Optional JSONL frame recording path")
    p.add_argument("--record-mode", choices=["jsonl", "txt", "txt-clean", "jsonl.gz", "txt.gz", "txt-clean.gz"], default="jsonl", help="Frame recording format")
    p.add_argument("--video-hook", default="", help="Optional shell command run after recording finishes")
    p.add_argument("--plugin", default="", help="Optional Python plugin file with hooks")
    p.add_argument("--replay-file", default="", help="Replay frames from a previous recording file")
    p.add_argument("--preset", choices=list(PRESETS.keys()), default="", help="Apply a visual preset")
    p.add_argument("--scene-sync", choices=["adaptive", "bpm", "hybrid"], default="adaptive", help="How scene changes synchronize")
    p.add_argument("--quality-mode", choices=["off", "auto"], default="auto", help="Adaptive quality control")
    p.add_argument("--ui-style", choices=["full", "minimal"], default="full", help="UI density profile")
    p.add_argument("--scene-pack", default="", help="Named scene pack")
    p.add_argument("--scene-pack-file", default="", help="JSON file with custom scene packs")
    p.add_argument("--save-scene-pack", default="", help="Write current active scene pack to JSON and exit")
    p.add_argument("--unicode-bars", action="store_true", help="Use Unicode block bars for meters")
    p.add_argument("--alert-tones", action="store_true", help="Enable event-linked terminal alert tones")
    p.add_argument("--mission-timeline", dest="mission_timeline", action="store_true", help="Enable mission timeline progression")
    p.add_argument("--no-mission-timeline", dest="mission_timeline", action="store_false", help="Disable mission timeline progression")
    p.add_argument("--defender-ai", dest="defender_ai", action="store_true", help="Enable defender countermeasure simulation")
    p.add_argument("--no-defender-ai", dest="defender_ai", action="store_false", help="Disable defender countermeasure simulation")
    p.add_argument("--audio-fx", dest="audio_fx", action="store_true", help="Enable audio-reactive terminal FX")
    p.add_argument("--no-audio-fx", dest="audio_fx", action="store_false", help="Disable audio-reactive terminal FX")
    p.add_argument("--diagnostics", action="store_true", help="Print startup diagnostics to stderr")
    p.add_argument("--setup-ui", dest="setup_ui", action="store_true", help="Open setup popup before running")
    p.add_argument("--no-setup-ui", dest="setup_ui", action="store_false", help="Skip setup popup before running")
    p.add_argument("--ui", dest="ui", action="store_true", help="Open single popup control window")
    p.add_argument("--no-ui", dest="ui", action="store_false", help="Disable popup control window")
    p.set_defaults(play=True, ui=True, mission_timeline=True, defender_ai=True, audio_fx=True, setup_ui=False)
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
    return args


def setup_run_with_ui(args: argparse.Namespace) -> bool:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except Exception:
        print("UI unavailable: tkinter is not installed", file=sys.stderr)
        return False

    root = tk.Tk()
    root.title("CMD-AUDIO Setup")
    root.resizable(True, True)
    root.minsize(720, 560)

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

    frm = ttk.Frame(root, padding=10)
    frm.grid(row=0, column=0, sticky="nsew")

    ttk.Label(frm, text="Source").grid(row=0, column=0, sticky="w")
    source_combo = ttk.Combobox(frm, textvariable=source_var, values=["file", "mic", "system"], state="readonly")
    source_combo.grid(row=0, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="Audio File").grid(row=1, column=0, sticky="w")
    audio_entry = ttk.Entry(frm, textvariable=audio_var)
    audio_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0))
    browse_btn = ttk.Button(
        frm,
        text="Browse...",
        command=lambda: audio_var.set(filedialog.askopenfilename() or audio_var.get()),
    )
    browse_btn.grid(row=1, column=2, sticky="w", padx=(8, 0))

    ttk.Label(frm, text="Capture Seconds").grid(row=2, column=0, sticky="w")
    ttk.Entry(frm, textvariable=capture_var).grid(row=2, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="FPS").grid(row=3, column=0, sticky="w")
    ttk.Entry(frm, textvariable=fps_var).grid(row=3, column=1, sticky="ew", padx=(8, 0))

    ttk.Checkbutton(frm, text="Play Audio", variable=play_var).grid(row=4, column=0, sticky="w", pady=(4, 0))

    ttk.Label(frm, text="Seed (optional)").grid(row=5, column=0, sticky="w")
    ttk.Entry(frm, textvariable=seed_var).grid(row=5, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="Sensitivity").grid(row=6, column=0, sticky="w")
    ttk.Entry(frm, textvariable=sensitivity_var).grid(row=6, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="Speed Min").grid(row=7, column=0, sticky="w")
    ttk.Entry(frm, textvariable=speed_min_var).grid(row=7, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="Speed Max").grid(row=8, column=0, sticky="w")
    ttk.Entry(frm, textvariable=speed_max_var).grid(row=8, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="Switch Min (s)").grid(row=9, column=0, sticky="w")
    ttk.Entry(frm, textvariable=switch_min_var).grid(row=9, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="Switch Max (s)").grid(row=10, column=0, sticky="w")
    ttk.Entry(frm, textvariable=switch_max_var).grid(row=10, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="Theme").grid(row=11, column=0, sticky="w")
    ttk.Combobox(frm, textvariable=theme_var, values=list(THEMES.keys()), state="readonly").grid(row=11, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="Preset").grid(row=12, column=0, sticky="w")
    ttk.Combobox(frm, textvariable=preset_var, values=[""] + list(PRESETS.keys()), state="readonly").grid(row=12, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="Scene Sync").grid(row=13, column=0, sticky="w")
    ttk.Combobox(frm, textvariable=scene_sync_var, values=["adaptive", "bpm", "hybrid"], state="readonly").grid(row=13, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="Quality").grid(row=14, column=0, sticky="w")
    ttk.Combobox(frm, textvariable=quality_var, values=["auto", "off"], state="readonly").grid(row=14, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="Banner Text").grid(row=15, column=0, sticky="w")
    ttk.Entry(frm, textvariable=banner_var).grid(row=15, column=1, sticky="ew", padx=(8, 0))
    ttk.Label(frm, text="Banner Align").grid(row=16, column=0, sticky="w")
    ttk.Combobox(frm, textvariable=banner_align_var, values=["left", "center", "right"], state="readonly").grid(row=16, column=1, sticky="ew", padx=(8, 0))
    ttk.Label(frm, text="Banner Animation").grid(row=17, column=0, sticky="w")
    ttk.Combobox(frm, textvariable=banner_anim_var, values=["off", "scroll", "pulse"], state="readonly").grid(row=17, column=1, sticky="ew", padx=(8, 0))
    ttk.Label(frm, text="Banner Size").grid(row=18, column=0, sticky="w")
    ttk.Combobox(frm, textvariable=banner_size_var, values=["normal", "large"], state="readonly").grid(row=18, column=1, sticky="ew", padx=(8, 0))
    ttk.Checkbutton(frm, text="Show Banner Row", variable=show_banner_var).grid(row=19, column=0, sticky="w", pady=(4, 0))

    ttk.Checkbutton(frm, text="Keep Converted WAV", variable=keep_converted_var).grid(row=20, column=0, sticky="w", pady=(4, 0))
    ttk.Checkbutton(frm, text="Print Diagnostics", variable=diagnostics_var).grid(row=21, column=0, sticky="w", pady=(4, 0))
    ttk.Checkbutton(frm, text="Alert Tones", variable=alert_tones_var).grid(row=20, column=1, sticky="w", padx=(8, 0), pady=(4, 0))
    ttk.Checkbutton(frm, text="Mission Timeline", variable=mission_timeline_var).grid(row=21, column=1, sticky="w", padx=(8, 0), pady=(4, 0))
    ttk.Checkbutton(frm, text="Defender AI", variable=defender_ai_var).grid(row=20, column=2, sticky="w", padx=(8, 0), pady=(4, 0))
    ttk.Checkbutton(frm, text="Audio FX", variable=audio_fx_var).grid(row=21, column=2, sticky="w", padx=(8, 0), pady=(4, 0))

    ttk.Label(frm, text="Record File").grid(row=22, column=0, sticky="w")
    ttk.Entry(frm, textvariable=record_file_var).grid(row=22, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="Record Mode").grid(row=23, column=0, sticky="w")
    ttk.Combobox(frm, textvariable=record_mode_var, values=["jsonl", "txt", "txt-clean", "jsonl.gz", "txt.gz", "txt-clean.gz"], state="readonly").grid(row=23, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="Playlist File").grid(row=24, column=0, sticky="w")
    ttk.Entry(frm, textvariable=playlist_var).grid(row=24, column=1, sticky="ew", padx=(8, 0))
    ttk.Button(
        frm,
        text="Browse...",
        command=lambda: playlist_var.set(filedialog.askopenfilename() or playlist_var.get()),
    ).grid(row=24, column=2, sticky="w", padx=(8, 0))

    ttk.Label(frm, text="Scene Pack").grid(row=25, column=0, sticky="w")
    ttk.Combobox(frm, textvariable=scene_pack_var, values=[""] + sorted(list(SCENE_PACKS.keys())), state="readonly").grid(row=25, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frm, text="Scene Pack File").grid(row=26, column=0, sticky="w")
    ttk.Entry(frm, textvariable=scene_pack_file_var).grid(row=26, column=1, sticky="ew", padx=(8, 0))
    ttk.Button(
        frm,
        text="Browse...",
        command=lambda: scene_pack_file_var.set(filedialog.askopenfilename() or scene_pack_file_var.get()),
    ).grid(row=26, column=2, sticky="w", padx=(8, 0))

    ttk.Label(frm, text="Plugin File").grid(row=27, column=0, sticky="w")
    ttk.Entry(frm, textvariable=plugin_var).grid(row=27, column=1, sticky="ew", padx=(8, 0))
    ttk.Button(
        frm,
        text="Browse...",
        command=lambda: plugin_var.set(filedialog.askopenfilename() or plugin_var.get()),
    ).grid(row=27, column=2, sticky="w", padx=(8, 0))

    ttk.Label(frm, text="Video Hook").grid(row=28, column=0, sticky="w")
    ttk.Entry(frm, textvariable=video_hook_var).grid(row=28, column=1, sticky="ew", padx=(8, 0))

    def update_source_state(*_: object) -> None:
        in_file_mode = source_var.get() == "file"
        state = "normal" if in_file_mode else "disabled"
        audio_entry.configure(state=state)
        browse_btn.configure(state=state)

    def start_run() -> None:
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

            audio_path = audio_var.get().strip()
            playlist_path = playlist_var.get().strip()
            if source == "file" and not audio_path and not playlist_path:
                messagebox.showerror("Missing Audio", "Audio file path or playlist file is required when source is file.")
                return

            args.source = source
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

    def cancel_run() -> None:
        root.destroy()

    source_var.trace_add("write", update_source_state)
    update_source_state()

    btn_row = ttk.Frame(frm)
    btn_row.grid(row=29, column=0, columnspan=3, sticky="e", pady=(10, 0))
    ttk.Button(btn_row, text="Cancel", command=cancel_run).pack(side="right")
    ttk.Button(btn_row, text="Start", command=start_run).pack(side="right", padx=(0, 8))

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    frm.columnconfigure(1, weight=1)
    root.protocol("WM_DELETE_WINDOW", cancel_run)

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

    # Null out the Tcl interpreter reference so GC-triggered __del__ from any
    # thread cannot reach the dead Tcl runtime (Python 3.14 compatibility).
    for _var in _setup_vars:
        try:
            _var._tk = None  # type: ignore[attr-defined]
        except Exception:
            pass

    return started[0]


@dataclass
class RuntimeSnapshot:
    sensitivity: float
    speed_min: float
    speed_max: float
    terminal_switch_min: float
    terminal_switch_max: float
    theme_name: str
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


class LiveControlState:
    def __init__(
        self,
        sensitivity: float,
        speed_min: float,
        speed_max: float,
        terminal_switch_min: float,
        terminal_switch_max: float,
        theme_name: str,
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
        with self._lock:
            self._sensitivity = clamp(v, 0.1, 4.0)

    def set_speed_bounds(self, speed_min: float, speed_max: float) -> None:
        with self._lock:
            min_v = clamp(speed_min, 0.05, 6.0)
            max_v = clamp(speed_max, min_v, 6.0)
            self._speed_min = min_v
            self._speed_max = max_v

    def set_terminal_switch_bounds(self, switch_min: float, switch_max: float) -> None:
        with self._lock:
            min_v = clamp(switch_min, 0.5, 60.0)
            max_v = clamp(switch_max, min_v, 60.0)
            self._terminal_switch_min = min_v
            self._terminal_switch_max = max_v

    def set_theme(self, theme_name: str) -> None:
        with self._lock:
            if theme_name in THEMES:
                self._theme_name = theme_name

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


@dataclass
class LiveUIHandle:
    stop_event: threading.Event
    thread: threading.Thread

    def close(self, timeout: float = 1.5) -> None:
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join(timeout=timeout)


def start_live_control_window(state: LiveControlState) -> Optional[LiveUIHandle]:
    try:
        import tkinter as tk
        from tkinter import filedialog, ttk
    except Exception:
        print("UI unavailable: tkinter is not installed", file=sys.stderr)
        return None

    stop_event = threading.Event()

    def ui_thread_main() -> None:
        try:
            root = tk.Tk()
        except Exception as exc:
            print(f"UI window unavailable: {exc}", file=sys.stderr)
            return
        root.title("CMD-AUDIO Live Controls")
        root.resizable(True, True)
        root.minsize(560, 520)

        ss = state.snapshot()
        sensitivity_var = tk.DoubleVar(value=ss.sensitivity)
        speed_min_var = tk.DoubleVar(value=ss.speed_min)
        speed_max_var = tk.DoubleVar(value=ss.speed_max)
        switch_min_var = tk.DoubleVar(value=ss.terminal_switch_min)
        switch_max_var = tk.DoubleVar(value=ss.terminal_switch_max)
        theme_var = tk.StringVar(value=ss.theme_name)
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

        frm = ttk.Frame(root, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frm, text="Sensitivity").grid(row=0, column=0, sticky="w")
        ttk.Scale(frm, from_=0.1, to=4.0, variable=sensitivity_var, orient="horizontal").grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(frm, text="Speed Min").grid(row=1, column=0, sticky="w")
        ttk.Scale(frm, from_=0.05, to=3.0, variable=speed_min_var, orient="horizontal").grid(row=1, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(frm, text="Speed Max").grid(row=2, column=0, sticky="w")
        ttk.Scale(frm, from_=0.5, to=6.0, variable=speed_max_var, orient="horizontal").grid(row=2, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(frm, text="Switch Min (s)").grid(row=3, column=0, sticky="w")
        ttk.Scale(frm, from_=0.5, to=20.0, variable=switch_min_var, orient="horizontal").grid(row=3, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(frm, text="Switch Max (s)").grid(row=4, column=0, sticky="w")
        ttk.Scale(frm, from_=1.0, to=60.0, variable=switch_max_var, orient="horizontal").grid(row=4, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(frm, text="Theme").grid(row=5, column=0, sticky="w")
        ttk.Combobox(frm, textvariable=theme_var, values=list(THEMES.keys()), state="readonly").grid(row=5, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(frm, text="Scene Sync").grid(row=6, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(frm, textvariable=scene_sync_var, values=["adaptive", "bpm", "hybrid"], state="readonly").grid(row=6, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Label(frm, text="UI Style").grid(row=7, column=0, sticky="w")
        ttk.Combobox(frm, textvariable=ui_style_var, values=["full", "minimal"], state="readonly").grid(row=7, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(frm, text="Quality").grid(row=8, column=0, sticky="w")
        ttk.Combobox(frm, textvariable=quality_mode_var, values=["auto", "off"], state="readonly").grid(row=8, column=1, sticky="ew", padx=(8, 0))

        ttk.Checkbutton(frm, text="Unicode Bars", variable=unicode_bars_var).grid(row=9, column=0, sticky="w", pady=(4, 0))

        ttk.Label(frm, text="Terminal Profile").grid(row=10, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(frm, textvariable=terminal_mode_var, values=list(TERMINAL_PROFILES.keys()), state="readonly").grid(row=10, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Label(frm, text="Operation Mode").grid(row=11, column=0, sticky="w")
        ttk.Combobox(frm, textvariable=operation_mode_var, values=OPERATION_MODES, state="readonly").grid(row=11, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(frm, text="Target Lock").grid(row=12, column=0, sticky="w")
        ttk.Combobox(frm, textvariable=target_lock_var, values=TARGETS, state="readonly").grid(row=12, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(frm, text="Current Music").grid(row=13, column=0, sticky="w", pady=(8, 0))
        ttk.Label(frm, textvariable=music_current_var).grid(row=13, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Label(frm, text="New Music File").grid(row=14, column=0, sticky="w")
        ttk.Entry(frm, textvariable=music_choice_var).grid(row=14, column=1, sticky="ew", padx=(8, 0))
        ttk.Button(
            frm,
            text="Browse...",
            command=lambda: music_choice_var.set(filedialog.askopenfilename() or music_choice_var.get()),
        ).grid(row=14, column=2, sticky="w", padx=(8, 0))

        ttk.Label(frm, text="Music Status").grid(row=15, column=0, sticky="w")
        ttk.Label(frm, textvariable=music_status_var).grid(row=15, column=1, sticky="w", padx=(8, 0))

        def load_music_file() -> None:
            choice = music_choice_var.get().strip()
            if not choice:
                music_status_var.set("Enter a file path first")
                return
            state.set_music_status("Loading requested...")
            state.request_music_change(choice)

        ttk.Button(frm, text="Load Music", command=load_music_file).grid(row=16, column=1, sticky="w", padx=(8, 0), pady=(4, 0))

        ttk.Label(frm, text="Banner Text").grid(row=17, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=banner_var).grid(row=17, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Label(frm, text="Banner Align").grid(row=18, column=0, sticky="w")
        ttk.Combobox(frm, textvariable=banner_align_var, values=["left", "center", "right"], state="readonly").grid(row=18, column=1, sticky="ew", padx=(8, 0))
        ttk.Label(frm, text="Banner Animation").grid(row=19, column=0, sticky="w")
        ttk.Combobox(frm, textvariable=banner_anim_var, values=["off", "scroll", "pulse"], state="readonly").grid(row=19, column=1, sticky="ew", padx=(8, 0))
        ttk.Label(frm, text="Banner Size").grid(row=20, column=0, sticky="w")
        ttk.Combobox(frm, textvariable=banner_size_var, values=["normal", "large"], state="readonly").grid(row=20, column=1, sticky="ew", padx=(8, 0))

        ttk.Checkbutton(frm, text="Show Banner", variable=show_banner_var).grid(row=21, column=0, sticky="w", pady=(4, 0))
        ttk.Checkbutton(frm, text="Alert Tones", variable=alert_tones_var).grid(row=21, column=1, sticky="w", pady=(4, 0), padx=(8, 0))
        ttk.Checkbutton(frm, text="Lock Scene", variable=lock_scene_var).grid(row=22, column=0, sticky="w", pady=(4, 0))
        ttk.Checkbutton(frm, text="Mission Timeline", variable=mission_timeline_var).grid(row=22, column=1, sticky="w", pady=(4, 0), padx=(8, 0))
        ttk.Checkbutton(frm, text="Pause", variable=paused_var).grid(row=23, column=0, sticky="w", pady=(8, 0))
        ttk.Checkbutton(frm, text="Defender AI", variable=defender_ai_var).grid(row=23, column=1, sticky="w", pady=(8, 0), padx=(8, 0))
        ttk.Checkbutton(frm, text="Audio FX", variable=audio_fx_var).grid(row=24, column=2, sticky="w", pady=(8, 0), padx=(8, 0))

        ttk.Label(frm, text="Frame Drops").grid(row=24, column=0, sticky="w", pady=(8, 0))
        ttk.Label(frm, textvariable=frame_drops_var).grid(row=24, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        def close_only() -> None:
            root.destroy()

        def quit_animation() -> None:
            state.request_quit()
            root.destroy()

        btn_row = ttk.Frame(frm)
        btn_row.grid(row=25, column=0, columnspan=3, sticky="e", pady=(10, 0))
        ttk.Button(btn_row, text="Close Window", command=close_only).pack(side="right")
        ttk.Button(btn_row, text="Stop Console", command=quit_animation).pack(side="right", padx=(0, 8))

        def sync_to_state(*_: object) -> None:
            state.set_sensitivity(float(sensitivity_var.get()))
            state.set_speed_bounds(float(speed_min_var.get()), float(speed_max_var.get()))
            state.set_terminal_switch_bounds(float(switch_min_var.get()), float(switch_max_var.get()))
            state.set_theme(theme_var.get())
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

        sensitivity_var.trace_add("write", sync_to_state)
        speed_min_var.trace_add("write", sync_to_state)
        speed_max_var.trace_add("write", sync_to_state)
        switch_min_var.trace_add("write", sync_to_state)
        switch_max_var.trace_add("write", sync_to_state)
        theme_var.trace_add("write", sync_to_state)
        scene_sync_var.trace_add("write", sync_to_state)
        ui_style_var.trace_add("write", sync_to_state)
        quality_mode_var.trace_add("write", sync_to_state)
        unicode_bars_var.trace_add("write", sync_to_state)
        alert_tones_var.trace_add("write", sync_to_state)
        mission_timeline_var.trace_add("write", sync_to_state)
        defender_ai_var.trace_add("write", sync_to_state)
        audio_fx_var.trace_add("write", sync_to_state)
        terminal_mode_var.trace_add("write", sync_to_state)
        operation_mode_var.trace_add("write", sync_to_state)
        target_lock_var.trace_add("write", sync_to_state)
        banner_var.trace_add("write", sync_to_state)
        banner_align_var.trace_add("write", sync_to_state)
        banner_anim_var.trace_add("write", sync_to_state)
        banner_size_var.trace_add("write", sync_to_state)
        show_banner_var.trace_add("write", sync_to_state)
        lock_scene_var.trace_add("write", sync_to_state)
        paused_var.trace_add("write", sync_to_state)

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
        frm.columnconfigure(1, weight=1)

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

        # Null out the Tcl interpreter reference on every Variable so that
        # GC-triggered __del__ calls from any thread cannot reach the dead
        # Tcl runtime (fixes "main thread is not in main loop" on Python 3.14).
        for _var in _tk_vars:
            try:
                _var._tk = None  # type: ignore[attr-defined]
            except Exception:
                pass

    t = threading.Thread(target=ui_thread_main, name="cmd-audio-ui", daemon=False)
    t.start()
    return LiveUIHandle(stop_event=stop_event, thread=t)


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def smooth(vals: List[float], radius: int = 2) -> List[float]:
    out: List[float] = []
    for i in range(len(vals)):
        a = max(0, i - radius)
        b = min(len(vals), i + radius + 1)
        s = vals[a:b]
        out.append(sum(s) / len(s))
    return out


def normalize(vals: List[float]) -> List[float]:
    lo = min(vals)
    hi = max(vals)
    span = hi - lo
    if span <= 1e-9:
        return [0.0 for _ in vals]
    return [math.sqrt(max(0.0, (v - lo) / span)) for v in vals]


def ensure_wav_input(audio_path: str, keep_converted: bool = False) -> Tuple[str, bool]:
    if audio_path.lower().endswith(".wav"):
        return audio_path, False

    tmp = tempfile.NamedTemporaryFile(prefix="hacker_sync_", suffix=".wav", delete=False)
    tmp_wav = tmp.name
    tmp.close()

    cmd = ["ffmpeg", "-y", "-i", audio_path, "-ac", "1", "-ar", "44100", tmp_wav]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except FileNotFoundError as exc:
        try:
            os.unlink(tmp_wav)
        except OSError:
            pass
        raise RuntimeError("Non-WAV input needs ffmpeg installed") from exc
    except subprocess.CalledProcessError as exc:
        try:
            os.unlink(tmp_wav)
        except OSError:
            pass
        raise RuntimeError("ffmpeg failed to convert input audio") from exc

    if keep_converted:
        print(f"Converted audio saved to: {tmp_wav}", file=sys.stderr)
        return tmp_wav, False
    return tmp_wav, True


def capture_to_wav(source: str, seconds: int) -> str:
    tmp = tempfile.NamedTemporaryFile(prefix=f"hacker_{source}_", suffix=".wav", delete=False)
    wav_out = tmp.name
    tmp.close()

    if source == "mic":
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "pulse",
            "-i",
            "default",
            "-t",
            str(seconds),
            "-ac",
            "1",
            "-ar",
            "44100",
            wav_out,
        ]
        arecord_cmd = ["arecord", "-q", "-f", "cd", "-d", str(seconds), wav_out]
        for cmd in (ffmpeg_cmd, arecord_cmd):
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return wav_out
            except FileNotFoundError:
                continue
            except subprocess.CalledProcessError:
                continue
    else:
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "pulse",
            "-i",
            "default",
            "-t",
            str(seconds),
            "-ac",
            "1",
            "-ar",
            "44100",
            wav_out,
        ]
        try:
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return wav_out
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

    try:
        os.unlink(wav_out)
    except OSError:
        pass
    raise RuntimeError("Could not capture audio source. Install ffmpeg or arecord.")


def prepare_audio_input(args: argparse.Namespace, audio_path: str) -> Tuple[str, str, bool]:
    if args.source == "file":
        if not audio_path:
            raise RuntimeError("Audio file path is required in file mode")
        if not os.path.exists(audio_path):
            raise RuntimeError(f"Audio file not found: {audio_path}")
        wav_input, cleanup = ensure_wav_input(audio_path, keep_converted=args.keep_converted)
        return wav_input, wav_input, cleanup

    captured = capture_to_wav(args.source, args.capture_seconds)
    print(f"Captured {args.source} audio to: {captured}", file=sys.stderr)
    return captured, captured, True


def decode_pcm_to_mono_samples(data: bytes, sample_width: int, channels: int) -> List[int]:
    if sample_width not in (1, 2, 3, 4):
        raise ValueError(f"Unsupported sample width: {sample_width} bytes")

    frame_size = sample_width * channels
    if frame_size <= 0 or len(data) % frame_size != 0:
        return []

    frame_count = len(data) // frame_size
    out: List[int] = []

    if sample_width == 1:
        for i in range(frame_count):
            offset = i * frame_size
            total = 0
            for c in range(channels):
                total += data[offset + c] - 128
            out.append(int(total / channels))
        return out

    if sample_width == 2:
        for i in range(frame_count):
            offset = i * frame_size
            total = 0
            for c in range(channels):
                ch_off = offset + (c * sample_width)
                total += struct.unpack_from("<h", data, ch_off)[0]
            out.append(int(total / channels))
        return out

    if sample_width == 3:
        for i in range(frame_count):
            offset = i * frame_size
            total = 0
            for c in range(channels):
                ch_off = offset + (c * sample_width)
                b0 = data[ch_off]
                b1 = data[ch_off + 1]
                b2 = data[ch_off + 2]
                unsigned = b0 | (b1 << 8) | (b2 << 16)
                signed = unsigned - 0x1000000 if unsigned & 0x800000 else unsigned
                total += signed
            out.append(int(total / channels))
        return out

    for i in range(frame_count):
        offset = i * frame_size
        total = 0
        for c in range(channels):
            ch_off = offset + (c * sample_width)
            total += struct.unpack_from("<i", data, ch_off)[0]
        out.append(int(total / channels))
    return out


def rms_from_samples(samples: List[int]) -> float:
    if not samples:
        return 0.0
    energy = 0.0
    for s in samples:
        energy += float(s * s)
    return math.sqrt(energy / len(samples))


def goertzel_power(samples: List[int], sample_rate: int, freq: float) -> float:
    if not samples:
        return 0.0
    omega = 2.0 * math.pi * (freq / float(sample_rate))
    coeff = 2.0 * math.cos(omega)
    s_prev = 0.0
    s_prev2 = 0.0
    for x in samples:
        s = float(x) + coeff * s_prev - s_prev2
        s_prev2 = s_prev
        s_prev = s
    power = s_prev2 * s_prev2 + s_prev * s_prev - coeff * s_prev * s_prev2
    return max(0.0, power)


def detect_beats(levels: List[float]) -> List[bool]:
    beats: List[bool] = []
    deltas = [0.0]
    for i in range(1, len(levels)):
        deltas.append(max(0.0, levels[i] - levels[i - 1]))

    for i in range(len(levels)):
        a = max(0, i - 12)
        b = max(1, i)
        baseline = sum(deltas[a:b]) / max(1, b - a)
        strong = deltas[i] > (baseline * 1.65 + 0.03)
        beats.append(strong and levels[i] > 0.35)
    return beats


def detect_fluxes(levels: List[float], bands: List[List[float]]) -> List[float]:
    if not levels:
        return []

    fluxes: List[float] = [0.0]
    for i in range(1, len(levels)):
        level_flux = max(0.0, levels[i] - levels[i - 1])
        if i < len(bands) and (i - 1) < len(bands):
            band_flux = sum(max(0.0, bands[i][j] - bands[i - 1][j]) for j in range(len(bands[i])))
            band_flux /= max(1, len(bands[i]))
        else:
            band_flux = 0.0
        fluxes.append(level_flux + band_flux)

    return normalize(smooth(fluxes, radius=2))


def normalize_band_matrix(bands: List[List[float]]) -> List[List[float]]:
    if not bands:
        return []
    band_count = len(bands[0])
    cols: List[List[float]] = [[row[i] for row in bands] for i in range(band_count)]
    norm_cols = [normalize(col) for col in cols]

    out: List[List[float]] = []
    for r in range(len(bands)):
        out.append([norm_cols[c][r] for c in range(band_count)])
    return out


def read_audio_features(wav_path: str, fps: int) -> AudioFeatures:
    with wave.open(wav_path, "rb") as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        total_frames = wf.getnframes()

        frames_per_bucket = max(1, sample_rate // fps)
        levels_raw: List[float] = []
        bands_raw: List[List[float]] = []

        while True:
            data = wf.readframes(frames_per_bucket)
            if not data:
                break

            samples = decode_pcm_to_mono_samples(data, sample_width, channels)
            rms = rms_from_samples(samples)
            levels_raw.append(rms)

            band_row: List[float] = []
            for f in FREQ_CENTERS:
                if f >= (sample_rate / 2.0):
                    band_row.append(0.0)
                else:
                    band_row.append(goertzel_power(samples, sample_rate, f))
            bands_raw.append(band_row)

    if not levels_raw:
        raise ValueError("No audio data found")

    levels_smooth = smooth(levels_raw, radius=2)
    levels = normalize(levels_smooth)
    bands = normalize_band_matrix(bands_raw)
    beats = detect_beats(levels)
    fluxes = detect_fluxes(levels, bands)
    beat_times = [i / float(fps) for i, is_beat in enumerate(beats) if is_beat]
    bpm_estimate = estimate_bpm(beat_times)
    duration = total_frames / float(sample_rate)
    return AudioFeatures(
        fps=fps,
        duration=duration,
        levels=levels,
        bands=bands,
        beats=beats,
        fluxes=fluxes,
        beat_times=beat_times,
        bpm_estimate=bpm_estimate,
    )


def make_demo_audio_features(fps: int, seconds: int = 180) -> AudioFeatures:
    frame_count = max(fps * max(10, seconds), fps)
    levels: List[float] = []
    bands: List[List[float]] = []
    beats: List[bool] = []
    fluxes: List[float] = []
    beat_times: List[float] = []

    bpm = 124.0
    beat_interval = 60.0 / bpm
    last_level = 0.0

    for i in range(frame_count):
        t = i / float(fps)
        is_beat = (t % beat_interval) < (1.0 / float(fps))

        groove = 0.45 + 0.28 * math.sin(2.0 * math.pi * 0.55 * t)
        wobble = 0.17 * math.sin(2.0 * math.pi * 0.11 * t + 1.2)
        sparkle = 0.08 * math.sin(2.0 * math.pi * 2.4 * t)
        beat_kick = 0.32 if is_beat else 0.0
        level = clamp(groove + wobble + sparkle + beat_kick, 0.0, 1.0)
        levels.append(level)

        band_row = [
            clamp(level * 0.90 + 0.10 * math.sin(2.0 * math.pi * 0.30 * t), 0.0, 1.0),
            clamp(level * 0.85 + 0.12 * math.sin(2.0 * math.pi * 0.38 * t + 0.8), 0.0, 1.0),
            clamp(level * 0.78 + 0.13 * math.sin(2.0 * math.pi * 0.72 * t + 1.1), 0.0, 1.0),
            clamp(level * 0.72 + 0.16 * math.sin(2.0 * math.pi * 1.10 * t + 0.2), 0.0, 1.0),
            clamp(level * 0.68 + 0.18 * math.sin(2.0 * math.pi * 1.45 * t + 1.7), 0.0, 1.0),
            clamp(level * 0.62 + 0.20 * math.sin(2.0 * math.pi * 2.10 * t + 0.4), 0.0, 1.0),
            clamp(level * 0.56 + 0.22 * math.sin(2.0 * math.pi * 2.90 * t + 2.0), 0.0, 1.0),
            clamp(level * 0.50 + 0.25 * math.sin(2.0 * math.pi * 3.40 * t + 2.4), 0.0, 1.0),
        ]
        bands.append(band_row)
        beats.append(is_beat)
        fluxes.append(max(0.0, level - last_level))
        if is_beat:
            beat_times.append(t)
        last_level = level

    return AudioFeatures(
        fps=fps,
        duration=frame_count / float(fps),
        levels=levels,
        bands=bands,
        beats=beats,
        fluxes=smooth(fluxes, radius=2),
        beat_times=beat_times,
        bpm_estimate=bpm,
    )


def estimate_bpm(beat_times: List[float]) -> float:
    if len(beat_times) < 4:
        return 0.0
    intervals: List[float] = []
    for i in range(1, len(beat_times)):
        dt = beat_times[i] - beat_times[i - 1]
        if 0.2 <= dt <= 2.0:
            intervals.append(dt)
    if not intervals:
        return 0.0
    avg = sum(intervals) / len(intervals)
    if avg <= 1e-6:
        return 0.0
    bpm = 60.0 / avg
    while bpm < 70.0:
        bpm *= 2.0
    while bpm > 180.0:
        bpm *= 0.5
    return bpm


def mission_timeline_from_progress(progress: float) -> MissionTimeline:
    p = clamp(progress, 0.0, 1.0)
    idx = min(len(MISSION_PHASES) - 1, int(p * len(MISSION_PHASES)))
    row = MISSION_PHASES[idx]
    return MissionTimeline(
        phase_idx=idx,
        phase_name=str(row["name"]),
        objective=str(row["objective"]),
        operation=str(row["operation"]),
        clearance=str(row["clearance"]),
        net_state=str(row["net_state"]),
    )


def maybe_apply_defender_countermeasure(
    level: float,
    beat: bool,
    flux: float,
    target_lock: str,
    terminal_mode: str,
    defender_pressure: float,
) -> Tuple[str, int, str, str, List[str]]:
    trigger_chance = (0.015 + (0.08 * level) + (0.07 * flux) + (0.05 if beat else 0.0)) * defender_pressure
    if random.random() > clamp(trigger_chance, 0.0, 0.45):
        return target_lock, 0, "stable", "", []

    action = random.choice(DEFENDER_ACTIONS)
    events: List[str] = []
    reroute_count = 0
    defender_state = action
    replacement_target = target_lock

    if action == "ip-ban-wave":
        choices = [t for t in TARGETS if t != target_lock]
        replacement_target = random.choice(choices) if choices else target_lock
        reroute_count = random.randint(1, 3)
        events.append(f"[!] defender: ban wave hit {target_lock}, rerouting via decoy")
        events.append(f"[*] fallback route established -> {replacement_target}")
    elif action == "port-rotation":
        reroute_count = 1
        events.append("[!] defender: service ports rotated mid-session")
        events.append("[*] adaptive scan retraining target fingerprints")
    elif action == "honeypot-lure":
        reroute_count = 2
        events.append("[!] defender: honeypot signature detected, abandoning node")
        events.append("[*] deception filter enabled, validating cert chain")
    else:
        reroute_count = random.randint(1, 2)
        events.append("[!] defender: traceback sweep active across uplinks")
        events.append("[*] proxy chain depth increased to evade capture")

    if random.random() < 0.55:
        events.extend(generate_shell_feed(level, True, terminal_mode)[:2])

    return replacement_target, reroute_count, defender_state, action, events


def should_shift_scene(
    scene_sync: str,
    beat: bool,
    flux: float,
    visual_t: float,
    next_scene_shift_at: float,
    bpm_phase_hit: bool,
) -> bool:
    if scene_sync == "bpm":
        return bpm_phase_hit
    if scene_sync == "hybrid":
        return bpm_phase_hit or beat or flux > 0.58 or visual_t >= next_scene_shift_at
    return beat or flux > 0.58 or visual_t >= next_scene_shift_at


def open_record_writer(path: str, mode: str) -> TextIO:
    if mode == "jsonl":
        return open(path, "w", encoding="utf-8")
    if mode in ("txt", "txt-clean"):
        return open(path, "w", encoding="utf-8")
    if mode in ("jsonl.gz", "txt.gz", "txt-clean.gz"):
        return gzip.open(path, "wt", encoding="utf-8")
    raise ValueError(f"Unsupported record mode: {mode}")


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)


def write_record_frame(rec: TextIO, mode: str, t: float, speed: float, frame: str) -> None:
    if mode.startswith("jsonl"):
        rec.write(json.dumps({"t": t, "speed": speed, "frame": frame}) + "\n")
        return
    if mode.startswith("txt-clean"):
        rec.write(f"--- frame t={t:.3f} speed={speed:.3f} ---\n")
        rec.write(strip_ansi(frame))
        rec.write("\n")
        return
    rec.write(f"--- frame t={t:.3f} speed={speed:.3f} ---\n")
    rec.write(frame)
    rec.write("\n")


def load_replay_frames(path: str) -> List[str]:
    opener = gzip.open if path.lower().endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        text = f.read()

    frames: List[str] = []
    if "\"frame\"" in text:
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            frame = row.get("frame")
            if isinstance(frame, str):
                frames.append(frame)
    else:
        parts = text.split("--- frame ")
        for part in parts:
            if "---\n" not in part:
                continue
            frames.append(part.split("---\n", 1)[1].rstrip("\n"))

    if not frames:
        raise ValueError("Replay file has no readable frames")
    return frames


def print_diagnostics(args: argparse.Namespace, audio_path: str, playback_path: str, audio: Optional[AudioFeatures]) -> None:
    term = shutil.get_terminal_size(fallback=(100, 30))
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    ffplay_ok = shutil.which("ffplay") is not None
    aplay_ok = shutil.which("aplay") is not None
    bpm = f"{audio.bpm_estimate:.1f}" if audio is not None and audio.bpm_estimate > 0 else "n/a"
    duration = f"{audio.duration:.2f}s" if audio is not None else "n/a"
    print("[diag] source=", args.source, file=sys.stderr)
    print("[diag] audio=", audio_path or "(none)", file=sys.stderr)
    print("[diag] playback=", playback_path or "(none)", file=sys.stderr)
    print("[diag] fps=", args.fps, " terminal=", f"{term.columns}x{term.lines}", file=sys.stderr)
    print("[diag] ffmpeg=", ffmpeg_ok, " ffplay=", ffplay_ok, " aplay=", aplay_ok, file=sys.stderr)
    print("[diag] duration=", duration, " bpm=", bpm, file=sys.stderr)


def launch_player(path: str) -> subprocess.Popen | None:
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


def fit_text(text: str, width: int) -> str:
    if width <= 0:
        return ""
    ansi_re = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

    def visible_len(s: str) -> int:
        return len(ansi_re.sub("", s))

    if visible_len(text) <= width:
        return text + (" " * (width - visible_len(text)))
    if width == 1:
        return "~"

    target = width - 1
    out = ""
    vis = 0
    i = 0
    while i < len(text) and vis < target:
        if text[i] == "\x1b":
            m = ansi_re.match(text, i)
            if m:
                out += m.group(0)
                i = m.end()
                continue
        out += text[i]
        vis += 1
        i += 1
    return out + "~"


def center_text(text: str, width: int) -> str:
    if width <= 0:
        return ""
    if len(text) >= width:
        return fit_text(text, width)
    left = max(0, (width - len(text)) // 2)
    right = width - len(text) - left
    return (" " * left) + text + (" " * right)


def align_text(text: str, width: int, align: str) -> str:
    clipped = fit_text(text, width)
    if align == "left":
        return clipped
    if align == "right":
        vis_len = len(re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text))
        if vis_len >= width:
            return clipped
        pad = " " * max(0, width - vis_len)
        return pad + text
    return center_text(text, width)


def prompt_banner_text(raw: RawInput, current_text: str) -> str:
    """Temporarily leave raw mode to let the user type a custom banner string."""
    try:
        raw.disable()
        sys.stdout.write(SHOW_CURSOR + RESET + "\n")
        sys.stdout.write(f"Banner text (blank keeps current) [{current_text}]: ")
        sys.stdout.flush()
        typed = sys.stdin.readline().rstrip("\n")
        if typed.strip():
            return typed.strip()[:120]
        return current_text
    finally:
        raw.enable()
        sys.stdout.write(HIDE_CURSOR)
        sys.stdout.flush()


BLOCK_FONT: dict = {
    " ": ["     ", "     ", "     ", "     ", "     "],
    "A": [" ### ", "#   #", "#####", "#   #", "#   #"],
    "B": ["#### ", "#   #", "#### ", "#   #", "#### "],
    "C": [" ####", "#    ", "#    ", "#    ", " ####"],
    "D": ["#### ", "#   #", "#   #", "#   #", "#### "],
    "E": ["#####", "#    ", "#### ", "#    ", "#####"],
    "F": ["#####", "#    ", "#### ", "#    ", "#    "],
    "G": [" ####", "#    ", "# ###", "#   #", " ####"],
    "H": ["#   #", "#   #", "#####", "#   #", "#   #"],
    "I": ["#####", "  #  ", "  #  ", "  #  ", "#####"],
    "J": ["  ###", "   # ", "   # ", "#  # ", " ##  "],
    "K": ["#   #", "#  # ", "###  ", "#  # ", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#####"],
    "M": ["#   #", "## ##", "# # #", "#   #", "#   #"],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", " ### "],
    "P": ["#### ", "#   #", "#### ", "#    ", "#    "],
    "Q": [" ### ", "#   #", "#   #", "#  ##", " ####"],
    "R": ["#### ", "#   #", "#### ", "#  # ", "#   #"],
    "S": [" ####", "#    ", " ### ", "    #", "#### "],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  "],
    "U": ["#   #", "#   #", "#   #", "#   #", " ### "],
    "V": ["#   #", "#   #", "#   #", " # # ", "  #  "],
    "W": ["#   #", "#   #", "# # #", "## ##", "#   #"],
    "X": ["#   #", " # # ", "  #  ", " # # ", "#   #"],
    "Y": ["#   #", " # # ", "  #  ", "  #  ", "  #  "],
    "Z": ["#####", "   # ", "  #  ", " #   ", "#####"],
    "0": [" ### ", "#  ##", "# # #", "##  #", " ### "],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", "#####"],
    "2": [" ### ", "#   #", "  ## ", " #   ", "#####"],
    "3": ["#### ", "    #", " ### ", "    #", "#### "],
    "4": ["#   #", "#   #", "#####", "    #", "    #"],
    "5": ["#####", "#    ", "#### ", "    #", "#### "],
    "6": [" ### ", "#    ", "#### ", "#   #", " ### "],
    "7": ["#####", "    #", "   # ", "  #  ", "  #  "],
    "8": [" ### ", "#   #", " ### ", "#   #", " ### "],
    "9": [" ### ", "#   #", " ####", "    #", " ### "],
    "-": ["     ", "     ", "#####", "     ", "     "],
    "_": ["     ", "     ", "     ", "     ", "#####"],
    ".": ["     ", "     ", "     ", " ##  ", " ##  "],
    "!": ["  #  ", "  #  ", "  #  ", "     ", "  #  "],
    "?": [" ### ", "#   #", "  ## ", "     ", "  #  "],
    ":": ["     ", " ##  ", "     ", " ##  ", "     "],
    "/": ["    #", "   # ", "  #  ", " #   ", "#    "],
    "+": ["     ", "  #  ", "#####", "  #  ", "     "],
    "*": ["# # #", " ### ", "#####", " ### ", "# # #"],
    "@": [" ### ", "#   #", "# ###", "# ###", " ##  "],
    "#": [" # # ", "#####", " # # ", "#####", " # # "],
}


def render_block_text(text: str) -> List[str]:
    """Render text as 5-row ASCII block letters. Each char is 6 columns (5 + 1 gap)."""
    rows = ["", "", "", "", ""]
    unknown = ["  ?  ", "  ?  ", "  ?  ", "     ", "  ?  "]
    for ch in text.upper():
        glyph = BLOCK_FONT.get(ch, unknown)
        for i in range(5):
            rows[i] += glyph[i] + " "
    return rows


def build_banner_line(text: str, width: int, align: str, anim: str, t: float, pulse: int) -> str:
    base = (text.strip() or "CMD-AUDIO ACTIVE")[:240]
    if anim == "scroll":
        padded = f"   {base}   "
        if not padded:
            return fit_text("", width)
        offset = int(t * 8.0) % len(padded)
        track = padded + padded
        return fit_text(track[offset: offset + width], width)
    if anim == "pulse":
        phase = math.sin(t * 5.0)
        marker = "*" if pulse > 0 else ("+" if phase > 0 else ".")
        decorated = f"{marker} {base} {marker}"
        return align_text(decorated, width, align)
    return align_text(base, width, align)


def build_banner_lines(text: str, width: int, align: str, anim: str, size: str, t: float, pulse: int) -> List[str]:
    if size != "large":
        return [build_banner_line(text, width, align, anim, t, pulse)]

    # Large mode: render 5-row ASCII block letters
    base = (text.strip() or "CMD-AUDIO ACTIVE")[:20]  # cap to avoid extreme width
    block_rows = render_block_text(base)  # list of 5 equal-length strings

    if anim == "scroll":
        # All 5 rows scroll together at the same offset
        padded = ["   " + r + "   " for r in block_rows]
        total = len(padded[0])
        offset = int(t * 6.0) % max(1, total)
        result = []
        for r in padded:
            doubled = r + r
            result.append(fit_text(doubled[offset: offset + width], width))
        return result

    if anim == "pulse":
        phase = math.sin(t * 5.0)
        marker = "*" if pulse > 0 else ("+" if phase > 0 else ".")
        result = []
        for r in block_rows:
            stripped = r.rstrip()
            line = f"{marker} {stripped} {marker}" if stripped.strip() else fit_text("", width)
            result.append(align_text(line, width, align))
        return result

    # off / static
    return [align_text(r, width, align) for r in block_rows]


def panel_box(title: str, width: int, height: int, body: List[str]) -> List[str]:
    width = max(8, width)
    height = max(3, height)
    inner_w = width - 2
    inner_h = height - 2

    label = f"[ {title.upper()} ]"
    if len(label) <= inner_w:
        left = max(0, (inner_w - len(label)) // 2)
        right = max(0, inner_w - len(label) - left)
        top_raw = ("=" * left) + label + ("=" * right)
    else:
        top_raw = "=" * inner_w
    top = f"{GREEN_DIM}+{top_raw}+{RESET}"
    bottom = f"{GREEN_DIM}+{'=' * inner_w}+{RESET}"

    lines: List[str] = [top]
    for i in range(inner_h):
        content = fit_text(body[i] if i < len(body) else "", inner_w)
        lines.append(f"{GREEN_DIM}|{RESET}{content}{GREEN_DIM}|{RESET}")
    lines.append(bottom)
    return lines


def meter_bar(fill_ratio: float, width: int) -> str:
    ratio = clamp(fill_ratio, 0.0, 1.0)
    bar_w = max(6, width)
    filled = int(round(ratio * bar_w))
    if USE_UNICODE_BARS:
        on_ch = "\u2588"
        off_ch = "\u2591"
    else:
        on_ch = CURRENT_STYLE["bar_on"]
        off_ch = CURRENT_STYLE["bar_off"]
    bar = (on_ch * filled) + (off_ch * (bar_w - filled))
    return f"[{bar}] {int(ratio * 100):3d}%"


def make_log_line(level: float, t: float, beat: bool) -> str:
    action = random.choice(LOG_ACTIONS)
    target = random.choice(ALERT_WORDS)
    strength = int(level * 100)
    marker = "!" if beat else " "
    host = random.choice(TARGETS)
    port = random.choice(PORTS)
    return f"{marker}{t:06.2f}s {action:<9} {target:<8} {host}:{port} pwr={strength:02d}%"


def make_incident_line(level: float, t: float, beat: bool, feed: IncidentFeedState) -> str:
    stages = [
        "probe accepted",
        "credential replay",
        "privilege pivot",
        "data siphon",
        "trace erasure",
    ]
    if feed.ttl <= 0 or random.random() < 0.1:
        feed.host = random.choice(TARGETS)
        feed.phase = 0
        feed.ttl = random.randint(4, 9)
    else:
        feed.phase = min(len(stages) - 1, feed.phase + (1 if random.random() < 0.45 or beat else 0))
        feed.ttl -= 1

    severity = "CRIT" if beat or level > 0.75 else "WARN" if level > 0.45 else "INFO"
    port = random.choice(PORTS)
    marker = "!" if beat else " "
    stage_text = stages[feed.phase]
    return f"{marker}{t:06.2f}s INCIDENT  {severity:<4} {feed.host}:{port} {stage_text}"


def random_ipv4() -> str:
    return ".".join(str(random.randint(10, 250)) for _ in range(4))


def generate_shell_feed(level: float, beat: bool, terminal_mode: str) -> List[str]:
    host = random.choice(TARGETS)
    ip = random_ipv4()
    port = random.choice(PORTS)
    profile = TERMINAL_PROFILES.get(terminal_mode) or TERMINAL_PROFILES["netrunner"]
    prompt = str(profile["prompt"])
    commands = [str(x) for x in profile["commands"]]
    statuses = [str(x) for x in profile["status"]]
    cmd = random.choice(commands).format(host=host)
    progress = int(level * 100)
    retry_count = random.randint(2, 14)

    lines = [
        f"{prompt} {cmd}",
        f"[*] routing via {ip}:{port}",
        f"[*] entropy-scan {host}  confidence={progress:02d}%",
    ]
    state_line = random.choice(statuses).format(host=host, count=retry_count)
    lines.append(state_line)
    if beat:
        lines.append(f"[+] beat lock acquired -> switching payload profile")

    return lines


def build_shell_feed(shell_lines: List[str], width: int, max_lines: int) -> List[str]:
    if max_lines <= 0:
        return []

    return [fit_text(line, width) for line in shell_lines[:max_lines]]


def render_network_nodes(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render Hacknet-style network node topology."""
    lines: List[str] = []
    node_count = min(5, max(3, height // 3))
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    rows = state.node_rows if state is not None and state.node_rows else []
    for i in range(node_count):
        if i < len(rows):
            node, port, breached = rows[i]
        else:
            node = random.choice(NODE_TYPES)
            port = random.choice(PORTS)
            breached = random.random() < activity
        status_text = "BREACHED" if breached else "SECURE"
        status = colorize_status(status_text, 0.95 if breached else 0.15)
        link_w = max(6, min(16, width // 6))
        link_fill = int(activity * link_w)
        connection = f"[{('=' * link_fill):<{link_w}}>]"
        line = f"{node:12} {port:4}  {status:8}  {connection}"
        lines.append(fit_text(line, width))
    lines.append(fit_text(f"Link load  {meter_bar(activity, max(8, width - 24))}", width))
    breach_ratio = sum(1 for _, _, breached in rows[:node_count] if breached) / max(1, node_count)
    lines.append(fit_text(f"Breach idx {meter_bar(breach_ratio, max(8, width - 24))}", width))
    if beat:
        lines.append(fit_text("[!] INTRUSION ALERT!", width))
    return lines[:height]


def render_file_transfer(
    level: float,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render file transfer progress bars."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    rows = state.file_rows if state is not None and state.file_rows else []
    file_count = min(3, max(1, height // 3))
    for i in range(file_count):
        file_name = rows[i] if i < len(rows) else random.choice(FILE_OPS)
        bar_w = max(10, width - 30)
        line = f"{file_name:20} {meter_bar(activity, bar_w)}"
        lines.append(fit_text(line, width))
    return lines[:height]


def render_firewall_status(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render firewall breach status."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    wall_state = state.firewall_state if state is not None and state.firewall_state else random.choice(FIREWALL_STATES)
    strength = int(activity * 100)
    
    header = f"FIREWALL: {wall_state} [{colorize_status(str(strength) + '%', activity)}]"
    lines.append(fit_text(header, width))
    
    bar_w = max(15, width - 10)
    lines.append(fit_text(f"BREACH {meter_bar(activity, bar_w)}", width))
    lines.append(fit_text(f"INTEGRITY {meter_bar(1.0 - activity, bar_w)}", width))
    
    if beat:
        lines.append(fit_text("[!] WALL DESTABILIZING", width))
    
    lines.append(fit_text(f"Port avail: {random.randint(2, 50)}", width))
    lines.append(fit_text(f"Exploits running: {max(1, int(activity * 6))}", width))
    
    return lines[:height]


def render_encryption_crack(
    level: float,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render encryption cracking progress."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    algo = state.crypto_algo if state is not None and state.crypto_algo else random.choice(ENCRYPTION_ALGOS)
    lines.append(fit_text(f"Algorithm: {algo}", width))
    
    keyspace = int((2**256) * activity)
    attempts = int(activity * 1000000)
    crack_pct = int(activity * 100)
    
    bar_w = max(15, width - 15)
    lines.append(fit_text(meter_bar(activity, bar_w), width))
    guess_ratio = clamp((activity * 0.92) + 0.06, 0.0, 1.0)
    lines.append(fit_text(f"Guess pass {meter_bar(guess_ratio, bar_w)}", width))
    lines.append(fit_text(f"Attempts: {attempts:,}", width))
    if crack_pct >= 100:
        lines.append(fit_text("[+] KEY RECOVERED!", width))
    
    return lines[:height]


def render_port_scan(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render port scan results."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    scanned = int(activity * 65535)
    lines.append(fit_text(f"NMAP SCAN: {scanned}/65535 ports", width))
    
    bar_w = max(12, width - 12)
    lines.append(fit_text(meter_bar(activity, bar_w), width))
    
    open_port_count = max(1, int(activity * 20))
    lines.append(fit_text(f"Open ports: {open_port_count}", width))
    lines.append(fit_text(f"Service map {meter_bar(open_port_count / 20.0, max(8, width - 16))}", width))
    
    rows = state.port_rows if state is not None and state.port_rows else []
    for i in range(min(3, height - 4)):
        if i < len(rows):
            port, service = rows[i]
        else:
            port = random.choice(PORTS)
            service = random.choice(["ssh", "http", "ftp", "smtp", "vnc", "xrdp"])
        line = f"  {port:5} {service:8} open"
        lines.append(fit_text(line, width))
    
    if beat:
        lines.append(fit_text("[+] VULNERABILITY FOUND!", width))
    
    return lines[:height]


def render_admin_alerts(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render admin detection and alert system."""
    lines: List[str] = []
    
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    alert_level = "CRITICAL" if beat else ("HIGH" if activity > 0.7 else "MEDIUM" if activity > 0.4 else "LOW")
    lines.append(fit_text(f"ALERT LEVEL: {colorize_status(alert_level, activity)}", width))
    lines.append(fit_text(f"Detect prob {meter_bar(activity, max(8, width - 16))}", width))
    
    rows = state.admin_rows if state is not None and state.admin_rows else []
    for i in range(min(4, height - 2)):
        if i < len(rows):
            alert = rows[i]
        else:
            port = random.choice(PORTS)
            alert = random.choice(ADMIN_NOTICES).format(port=port, count=random.randint(1, 100))
        lines.append(fit_text(alert[:width-2], width))
    
    if beat:
        lines.append(fit_text("[!] ADMIN ONLINE!", width))
    
    return lines[:height]


def compute_speed_factor(
    level: float,
    transient: float,
    flux: float,
    beat: bool,
    speed_min: float,
    speed_max: float,
) -> float:
    beat_bonus = 0.75 if beat else 0.0
    return clamp((0.30 + (1.55 * level) + (2.2 * transient) + (1.8 * flux) + beat_bonus), speed_min, speed_max)


def update_logs(
    logs: List[str],
    level: float,
    t: float,
    beat: bool,
    max_items: int,
    speed_factor: float,
    budget: float,
    incident_feed: IncidentFeedState,
) -> float:
    budget += (0.30 + (0.75 * level)) * speed_factor
    pushed = 0
    while budget >= 1.0 and pushed < 4:
        if random.random() < 0.65:
            logs.append(make_incident_line(level, t, beat, incident_feed))
        else:
            logs.append(make_log_line(level, t, beat))
        budget -= 1.0
        pushed += 1
    if len(logs) > max_items:
        del logs[: len(logs) - max_items]
    return budget


def build_spectrum_lines(
    bands: List[float],
    width: int,
    height: int,
    history: List[float],
    shell_lines: List[str],
    quality_scale: float,
) -> List[str]:
    bar_w = max(8, int((width - 20) * quality_scale))
    lines: List[str] = []

    band_count = min(len(bands), max(4, int((height - 4) * quality_scale)))
    bar_on = CURRENT_STYLE["bar_on"]
    bar_off = CURRENT_STYLE["bar_off"]
    spark_lut = CURRENT_STYLE["spark"]
    for i in range(band_count):
        b = clamp(bands[i], 0.0, 1.0)
        filled = int(b * bar_w)
        bar = (bar_on * filled) + (bar_off * (bar_w - filled))
        lines.append(f"B{i + 1:02d} [{bar}] {int(b * 100):3d}%")

    hist_w = max(10, min(width - 10, len(history)))
    hist = history[-hist_w:]
    spark = "".join(spark_lut[min(9, int(v * 9.99))] for v in hist)
    lines.append("")
    lines.append(f"history {spark}")
    room = height - len(lines)
    if room > 0:
        lines.extend(build_shell_feed(shell_lines, width, room))
    return lines[:height]


def build_telemetry_lines(
    level: float,
    t: float,
    duration: float,
    width: int,
    pulse: int,
    speed_factor: float,
    sensitivity: float,
    theme_name: str,
    terminal_mode: str,
    switch_min: float,
    switch_max: float,
    daemon: str,
    clearance: str,
    open_ports: int,
    trace_hops: int,
    packet: int,
    flux: float,
    mission_phase: str,
    mission_objective: str,
    defender_state: str,
    keys_line: str,
) -> List[str]:
    progress = clamp(t / duration if duration > 0 else 0.0, 0.0, 1.0)
    prog_w = max(8, width - 14)
    mini_w = max(8, width - 18)
    status = "LOCKED" if pulse > 0 else "TRACK"
    mood = "PEAK" if level > 0.75 else "FLOW" if level > 0.45 else "LOW"
    entropy = 3.2 + (level * 4.7)
    trace_ratio = clamp(trace_hops / 12.0, 0.0, 1.0)

    return [
        f"time     {t:7.2f}s / {duration:7.2f}s",
        f"level    {int(level * 100):3d}%   mood {mood}",
        f"status   {status}",
        f"clear    {clearance}",
        f"mission  {mission_phase}",
        f"defense  {defender_state}",
        f"daemon   {daemon}",
        f"ports    {open_ports:2d} open",
        f"trace    {trace_hops:2d} hops",
        f"speed    x{speed_factor:0.2f}",
        f"level m  {meter_bar(level, mini_w)}",
        f"flux m   {meter_bar(flux, mini_w)}",
        f"trace m  {meter_bar(trace_ratio, mini_w)}",
        f"sens     x{sensitivity:0.2f}",
        f"theme    {theme_name}",
        f"term     {terminal_mode}",
        f"switch   {switch_min:0.1f}-{switch_max:0.1f}s",
        f"entropy  {entropy:4.2f} bits",
        f"packet   {packet:5d} bytes",
        fit_text(f"obj      {mission_objective}", width),
        "",
        f"progress {meter_bar(progress, prog_w)}",
        "",
        keys_line,
    ]


def compute_quality_scale(quality_mode: str, dropped_frames: int) -> float:
    if quality_mode != "auto":
        return 1.0
    if dropped_frames > 220:
        return 0.55
    if dropped_frames > 120:
        return 0.70
    if dropped_frames > 50:
        return 0.85
    return 1.0


def pick_hacknet_visual_mode(visual_t: float) -> str:
    """Cycle through different Hacknet-style visualizations."""
    modes = ["spectrum", "nodes", "files", "firewall", "crypto", "ports", "admin"]
    mode_cycle_time = 4.0
    idx = int(visual_t / mode_cycle_time) % len(modes)
    return modes[idx]


def render_visual_mode(
    mode: str,
    level: float,
    beat: bool,
    bands: List[float],
    history: List[float],
    shell_lines: List[str],
    width: int,
    height: int,
    quality_scale: float,
) -> List[str]:
    """Render current Hacknet visual mode."""
    if mode == "nodes":
        return render_network_nodes(level, beat, width, height)
    elif mode == "files":
        return render_file_transfer(level, width, height)
    elif mode == "firewall":
        return render_firewall_status(level, beat, width, height)
    elif mode == "crypto":
        return render_encryption_crack(level, width, height)
    elif mode == "ports":
        return render_port_scan(level, beat, width, height)
    elif mode == "admin":
        return render_admin_alerts(level, beat, width, height)
    else:
        return build_spectrum_lines(bands, width, height, history, shell_lines, quality_scale)


def render_multi_visual_modes(
    level: float,
    beat: bool,
    bands: List[float],
    history: List[float],
    shell_lines: List[str],
    width: int,
    height: int,
    quality_scale: float,
) -> List[str]:
    """Render multiple Hacknet modes stacked vertically."""
    modes = ["nodes", "firewall", "ports", "crypto"]
    lines: List[str] = []
    
    if height < 8:
        return render_visual_mode("spectrum", level, beat, bands, history, shell_lines, width, height, quality_scale)
    
    section_height = max(2, height // len(modes))
    
    for mode in modes:
        mode_lines = render_visual_mode(mode, level, beat, bands, history, shell_lines, width, section_height, quality_scale)
        lines.extend(mode_lines)
        if len(lines) >= height:
            break
    
    return lines[:height]


def render_paneled_visuals(
    level: float,
    beat: bool,
    bands: List[float],
    history: List[float],
    shell_lines: List[str],
    width: int,
    height: int,
    quality_scale: float,
    module_levels: Dict[str, float],
    state: Optional[VisualState],
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Render separate Hacknet feeds sized for embedding in a composed center panel."""
    del bands, history, shell_lines, quality_scale
    panel_w = max(10, width)
    panel_h = max(2, height)

    nodes = render_network_nodes(level, beat, panel_w, panel_h, state=state, module_level=module_levels.get("nodes", level))
    firewall = render_firewall_status(level, beat, panel_w, panel_h, state=state, module_level=module_levels.get("firewall", level))
    ports = render_port_scan(level, beat, panel_w, panel_h, state=state, module_level=module_levels.get("ports", level))
    crypto = render_encryption_crack(level, panel_w, panel_h, state=state, module_level=module_levels.get("crypto", level))

    return nodes, firewall, ports, crypto


def refresh_visual_state(
    state: VisualState,
    module_levels: Dict[str, float],
    beat: bool,
    flux: float,
    t: float,
) -> None:
    churn = 0.10 + (0.35 * module_levels.get("nodes", 0.0)) + (0.25 * flux)
    if (t - state.last_refresh) < 0.22 and not beat:
        return

    target_nodes = 5
    if not state.node_rows:
        state.node_rows = [(random.choice(NODE_TYPES), random.choice(PORTS), random.random() < module_levels.get("nodes", 0.0)) for _ in range(target_nodes)]
    else:
        next_rows: List[Tuple[str, str, bool]] = []
        for node, port, breached in state.node_rows[:target_nodes]:
            if random.random() < churn:
                node = random.choice(NODE_TYPES)
            if random.random() < churn:
                port = random.choice(PORTS)
            if random.random() < (0.08 + (0.60 * module_levels.get("nodes", 0.0))):
                breached = not breached
            next_rows.append((node, port, breached))
        while len(next_rows) < target_nodes:
            next_rows.append((random.choice(NODE_TYPES), random.choice(PORTS), random.random() < module_levels.get("nodes", 0.0)))
        state.node_rows = next_rows

    if (not state.file_rows) or random.random() < (0.15 + (0.35 * module_levels.get("files", 0.0))):
        state.file_rows = random.sample(FILE_OPS, k=min(4, len(FILE_OPS)))

    if random.random() < (0.18 + (0.55 * module_levels.get("firewall", 0.0))):
        if module_levels.get("firewall", 0.0) > 0.7:
            state.firewall_state = random.choice(["WALL_BREACH", "ICE_DETECTED", "FIREWALL_DOWN"])
        else:
            state.firewall_state = random.choice(FIREWALL_STATES)

    if random.random() < (0.15 + (0.55 * module_levels.get("crypto", 0.0))):
        state.crypto_algo = random.choice(ENCRYPTION_ALGOS)

    if (not state.port_rows) or random.random() < (0.14 + (0.45 * module_levels.get("ports", 0.0))):
        services = ["ssh", "http", "ftp", "smtp", "vnc", "xrdp"]
        state.port_rows = [(random.choice(PORTS), random.choice(services)) for _ in range(4)]

    if (not state.admin_rows) or random.random() < (0.12 + (0.40 * module_levels.get("admin", 0.0))):
        state.admin_rows = [
            random.choice(ADMIN_NOTICES).format(port=random.choice(PORTS), count=random.randint(1, 100))
            for _ in range(4)
        ]

    state.last_refresh = t


def compose_center_panel(
    center_w: int,
    center_h: int,
    nodes: List[str],
    firewall: List[str],
    ports: List[str],
    crypto: List[str],
) -> List[str]:
    """Compose four separated hacking modules into a single center panel body."""
    if center_h <= 0:
        return []

    out: List[str] = []
    sections = [
        ("nodes", nodes),
        ("firewall", firewall),
        ("ports", ports),
        ("crypto", crypto),
    ]
    sec_h = max(2, center_h // len(sections))

    for idx, (name, lines) in enumerate(sections):
        label = f"< {name.upper()} >"
        edge_w = max(1, (center_w - len(label)) // 2)
        header_raw = ("-" * edge_w) + label + ("-" * max(1, center_w - edge_w - len(label)))
        out.append(f"{GREEN_DIM}{fit_text(header_raw, center_w)}{RESET}")

        usable = max(1, sec_h - 2)
        used = 0
        for line in lines[:usable]:
            out.append(fit_text(line, center_w))
            used += 1
        # Keep each module vertically filled without drawing dotted placeholders.
        fill_line = fit_text("", center_w)
        while used < usable:
            out.append(fill_line)
            used += 1
        if idx < len(sections) - 1:
            sep_raw = ":" * max(1, center_w)
            out.append(f"{GREEN_DARK}{fit_text(sep_raw, center_w)}{RESET}")

    return out[:center_h]


def apply_terminal_fx(rows: List[str], width: int, glitch_frames: int, scanline_flash: int, jitter: int) -> List[str]:
    if not rows:
        return rows

    out = list(rows)
    if glitch_frames > 0 and len(out) > 6:
        tear_line = random.randint(2, len(out) - 3)
        tear = fit_text(f"{GREEN_BRIGHT}//// SIGNAL TEAR DETECTED ////{RESET}", width)
        out[tear_line] = tear

    if scanline_flash > 0:
        for i in range(2, len(out) - 2, 3):
            out[i] = f"{GREEN_DARK}{fit_text(out[i], width)}{RESET}"

    if jitter > 0:
        pad = " " * min(2, jitter)
        out = [fit_text(pad + line, width) for line in out]

    return out


def render_frame(
    width: int,
    height: int,
    level: float,
    t: float,
    duration: float,
    logs: List[str],
    history: List[float],
    pulse: int,
    speed_factor: float,
    bands: List[float],
    sensitivity: float,
    theme_name: str,
    terminal_mode: str,
    switch_min: float,
    switch_max: float,
    operation_mode: str,
    target_lock: str,
    net_state: str,
    shell_lines: List[str],
    daemon: str,
    clearance: str,
    open_ports: int,
    trace_hops: int,
    packet: int,
    flux: float,
    mission_phase: str,
    mission_objective: str,
    defender_state: str,
    glitch_frames: int,
    scanline_flash: int,
    jitter: int,
    banner_text: str,
    banner_align: str,
    banner_anim: str,
    banner_size: str,
    show_banner: bool,
    quality_scale: float,
    keys_line: str,
    module_levels: Dict[str, float],
    visual_state: Optional[VisualState],
    ui_style: str,
) -> str:
    header = f"{GREEN_BRIGHT}CMD-AUDIO :: MUSIC SYNC CONSOLE :: {operation_mode}{RESET}"
    beat = colorize_status("BEAT", 0.95) if pulse > 0 else f"{GREEN_DARK}IDLE{RESET}"
    top_rule = f"{GREEN_DIM}{'=' * max(1, width)}{RESET}"
    mode_tag = "MIN" if ui_style == "minimal" else "FULL"
    head_line = fit_text(
        f"{header}   {beat}   lock:{target_lock}   mission:{mission_phase}   theme:{theme_name}   term:{terminal_mode}   ui:{mode_tag}",
        width,
    )

    body_h = max(6, height - 4)

    # Reserve rows for the banner so the frame doesn't overflow the terminal.
    if show_banner or banner_text.strip():
        banner_row_count = 5 if banner_size == "large" else 1
        body_h = max(6, body_h - banner_row_count)

    left_w = max(24, width // 3)
    right_w = max(24, width // 4)
    center_w = max(24, width - left_w - right_w - 2)

    nodes, firewall, ports, crypto = render_paneled_visuals(
        level,
        pulse > 0,
        bands,
        history,
        shell_lines,
        center_w - 2,
        max(2, (body_h - 2) // 4),
        quality_scale,
        module_levels,
        visual_state,
    )
    center_lines = compose_center_panel(center_w - 2, body_h - 2, nodes, firewall, ports, crypto)

    left_lines = logs[-(body_h - 2):]
    right_lines = build_telemetry_lines(
        level,
        t,
        duration,
        right_w - 2,
        pulse,
        speed_factor,
        sensitivity,
        theme_name,
        terminal_mode,
        switch_min,
        switch_max,
        daemon,
        clearance,
        open_ports,
        trace_hops,
        packet,
        flux,
        mission_phase,
        mission_objective,
        defender_state,
        keys_line,
    )

    rows: List[str] = [top_rule, head_line]
    if show_banner or banner_text.strip():
        banner_lines = build_banner_lines(banner_text, width, banner_align, banner_anim, banner_size, t, pulse)
        for banner_line in banner_lines:
            rows.append(f"{GREEN_BRIGHT}{banner_line}{RESET}")

    if ui_style == "minimal" or width < 100:
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

    pulse_word = random.choice(ALERT_WORDS) if pulse > 0 else "SYNC"
    footer_meter_w = max(10, width - 44)
    footer_net = colorize_status(net_state, 0.92 if "COLLAPSE" in net_state else 0.20)
    footer = fit_text(
        f"{GREEN_BRIGHT}::{pulse_word:<8}::{RESET} {meter_bar(level, footer_meter_w)}  flux:{int(flux * 100):3d}%  {footer_net}",
        width,
    )
    rows.append(footer)
    rows.append(top_rule)
    rows = apply_terminal_fx(rows, width, glitch_frames, scanline_flash, jitter)
    return "\n".join(rows)


def clear_and_home() -> None:
    sys.stdout.write(CLEAR)
    sys.stdout.flush()


def main() -> int:
    args = parse_args()

    if args.setup_ui:
        started = setup_run_with_ui(args)
        if not started:
            return 0

    plugin_module: Any = None
    if args.plugin:
        try:
            plugin_module = load_plugin_module(args.plugin)
        except Exception as exc:
            print(f"Plugin error: {exc}", file=sys.stderr)
            return 1

    custom_scene_packs: Dict[str, Dict[str, Any]] = {}
    if args.scene_pack_file:
        try:
            custom_scene_packs = load_scene_packs(args.scene_pack_file)
        except (OSError, ValueError) as exc:
            print(f"Scene pack error: {exc}", file=sys.stderr)
            return 1

    active_scene_pack_name = args.scene_pack.strip()
    all_scene_packs = dict(SCENE_PACKS)
    all_scene_packs.update(custom_scene_packs)
    scene_pack_weights = {
        "nodes": 1.0,
        "files": 1.0,
        "firewall": 1.0,
        "ports": 1.0,
        "crypto": 1.0,
        "admin": 1.0,
    }

    if active_scene_pack_name:
        chosen_pack = all_scene_packs.get(active_scene_pack_name)
        if chosen_pack is None:
            print(f"Unknown scene pack: {active_scene_pack_name}", file=sys.stderr)
            return 1
        scene_pack_weights = apply_scene_pack(args, chosen_pack)

    if args.save_config:
        config_payload = {
            "audio": " ".join(args.audio).strip(),
            "source": args.source,
            "playlist": args.playlist,
            "capture_seconds": args.capture_seconds,
            "fps": args.fps,
            "play": args.play,
            "seed": args.seed,
            "sensitivity": args.sensitivity,
            "speed_min": args.speed_min,
            "speed_max": args.speed_max,
            "terminal_switch_min": args.terminal_switch_min,
            "terminal_switch_max": args.terminal_switch_max,
            "theme": args.theme,
            "preset": args.preset,
            "scene_sync": args.scene_sync,
            "quality_mode": args.quality_mode,
            "ui_style": args.ui_style,
            "scene_pack": active_scene_pack_name,
            "scene_pack_file": args.scene_pack_file,
            "unicode_bars": args.unicode_bars,
            "alert_tones": args.alert_tones,
            "mission_timeline": args.mission_timeline,
            "defender_ai": args.defender_ai,
            "audio_fx": args.audio_fx,
            "banner_text": args.banner_text,
            "banner_align": args.banner_align,
            "banner_anim": args.banner_anim,
            "banner_size": args.banner_size,
            "show_banner": args.show_banner,
            "keep_converted": args.keep_converted,
            "record_file": args.record_file,
            "record_mode": args.record_mode,
            "video_hook": args.video_hook,
            "plugin": args.plugin,
            "setup_ui": args.setup_ui,
            "ui": args.ui,
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
                    "scene_sync": args.scene_sync,
                    "quality_mode": args.quality_mode,
                    "ui_style": args.ui_style,
                    "module_weights": scene_pack_weights,
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
    initial_music_file = " ".join(args.audio).strip() or "(demo mode)"

    def close_live_ui() -> None:
        if live_ui is not None:
            live_ui.close()
    args.terminal_switch_min = clamp(args.terminal_switch_min, 0.5, 60.0)
    args.terminal_switch_max = clamp(args.terminal_switch_max, args.terminal_switch_min, 60.0)
    if args.ui:
        live_state = LiveControlState(
            args.sensitivity,
            args.speed_min,
            args.speed_max,
            args.terminal_switch_min,
            args.terminal_switch_max,
            theme_name,
            args.banner_text,
            args.banner_align,
            args.banner_anim,
            args.banner_size,
            bool(args.show_banner),
            args.ui_style,
            args.quality_mode,
            bool(args.unicode_bars),
            args.scene_sync,
            bool(args.alert_tones),
            bool(args.mission_timeline),
            bool(args.defender_ai),
            bool(args.audio_fx),
            "netrunner",
            OPERATION_MODES[0],
            TARGETS[0],
            False,
            initial_music_file,
        )

    if args.seed is not None:
        random.seed(args.seed)

    if args.replay_file:
        try:
            replay_frames = load_replay_frames(args.replay_file)
        except (OSError, ValueError) as exc:
            print(f"Replay error: {exc}", file=sys.stderr)
            close_live_ui()
            return 1
        raw = RawInput()
        raw.enable()
        sys.stdout.write(HIDE_CURSOR)
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
                status = f"\n{GREEN_DIM}replay: idx={replay_idx + 1}/{len(replay_frames)} speed={replay_speed:.2f}x {'PAUSED' if paused_replay else 'PLAY'} keys:q p . , [ ] f b{RESET}"
                sys.stdout.write(status)
                sys.stdout.flush()
                if paused_replay:
                    time.sleep(0.03)
                    continue
                time.sleep(frame_time / replay_speed)
                replay_idx += 1
        finally:
            raw.disable()
            sys.stdout.write(SHOW_CURSOR + RESET + "\n")
            sys.stdout.flush()
            close_live_ui()
        return 0

    audio_path = " ".join(args.audio).strip()
    playlist_tracks: List[str] = []
    playlist_index = -1

    if args.source == "file":
        if args.playlist:
            try:
                playlist_tracks = load_playlist_file(args.playlist)
            except (OSError, ValueError) as exc:
                print(f"Playlist error: {exc}", file=sys.stderr)
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
            print(str(exc), file=sys.stderr)
            close_live_ui()
            return 1

        try:
            audio = read_audio_features(wav_input, args.fps)
        except KeyboardInterrupt:
            print("Interrupted during audio analysis.", file=sys.stderr)
            close_live_ui()
            if cleanup_wav:
                try:
                    os.unlink(wav_input)
                except OSError:
                    pass
            return 130
        except (wave.Error, ValueError) as exc:
            print(f"Failed to read audio: {exc}", file=sys.stderr)
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

    rec: Optional[TextIO] = None
    if args.record_file:
        try:
            rec = open_record_writer(args.record_file, args.record_mode)
        except (OSError, ValueError) as exc:
            print(f"Record error: {exc}", file=sys.stderr)
            close_live_ui()
            return 1

    raw = RawInput()
    raw.enable()

    sys.stdout.write(HIDE_CURSOR)
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
        node_rows=[],
        file_rows=[],
        firewall_state=random.choice(FIREWALL_STATES),
        crypto_algo=random.choice(ENCRYPTION_ALGOS),
        port_rows=[],
        admin_rows=[],
        last_refresh=0.0,
    )

    keys_line = "keys: q p +/- [ ] t b e c v x m r z 0 n u 1 2 3 a y k j g h o l"
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
        if not os.path.exists(new_music):
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
            logs = [
                " 000.00s Boot      CONSOLE  pwr=00%",
                " 000.01s Route     MATRIX   pwr=00%",
                " 000.02s Cipher    PRIME    pwr=00%",
            ]
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
                if snap.unicode_bars != USE_UNICODE_BARS:
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
                logs = [
                    " 000.00s Boot      CONSOLE  pwr=00%",
                    " 000.01s Route     MATRIX   pwr=00%",
                    " 000.02s Cipher    PRIME    pwr=00%",
                ]
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
                sensitivity = DEFAULTS["sensitivity"]
                args.speed_min = DEFAULTS["speed_min"]
                args.speed_max = DEFAULTS["speed_max"]
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
                set_bar_mode(not USE_UNICODE_BARS)
                if live_state is not None:
                    live_state.set_unicode_bars(USE_UNICODE_BARS)
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
                logs.append(
                    f"!{visual_t:06.2f}s Mission   {mission.phase_name:<8} obj={mission.objective[:28]}"
                )
                operation_mode = mission.operation
                clearance = mission.clearance
                net_state = mission.net_state
                shell_lines = generate_shell_feed(level, True, terminal_mode)
                if alert_tones_enabled and visual_t >= tone_cooldown_until:
                    sys.stdout.write("\a")
                    tone_cooldown_until = visual_t + 0.35
                if plugin_module is not None and hasattr(plugin_module, "on_event"):
                    try:
                        plugin_module.on_event(
                            {
                                "type": "mission_phase_change",
                                "phase": mission.phase_name,
                                "objective": mission.objective,
                                "t": visual_t,
                            }
                        )
                    except Exception:
                        pass
            elif not mission_timeline_enabled:
                mission_phase_name = "MANUAL"
                mission_objective = "timeline disabled"

            bass = sum(bands[:2]) / max(1, len(bands[:2]))
            mids = sum(bands[2:5]) / max(1, len(bands[2:5]))
            highs = sum(bands[5:]) / max(1, len(bands[5:]))
            module_levels = {
                "nodes": clamp(((0.40 * level) + (0.95 * mids)) * scene_pack_weights["nodes"], 0.0, 1.0),
                "files": clamp(((0.50 * level) + (0.25 * mids) + (0.25 * highs)) * scene_pack_weights["files"], 0.0, 1.0),
                "firewall": clamp(((0.35 * level) + (1.00 * bass)) * scene_pack_weights["firewall"], 0.0, 1.0),
                "ports": clamp(((0.30 * level) + (0.85 * bass)) * scene_pack_weights["ports"], 0.0, 1.0),
                "crypto": clamp(((0.30 * level) + (1.00 * highs)) * scene_pack_weights["crypto"], 0.0, 1.0),
                "admin": clamp(((0.45 * level) + (0.70 * highs)) * scene_pack_weights["admin"], 0.0, 1.0),
            }

            transient = abs(level - prev_level)
            speed_factor = compute_speed_factor(level, transient, flux, beat, args.speed_min, args.speed_max)
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

            if beat or flux > 0.45 or visual_t >= next_shell_refresh_at:
                shell_lines = generate_shell_feed(level, beat, terminal_mode)
                next_shell_refresh_at = visual_t + random.uniform(0.45, 1.6)

            if defender_ai_enabled:
                updated_target, reroute_hops, new_defender_state, defense_action, defense_events = maybe_apply_defender_countermeasure(
                    level=level,
                    beat=beat,
                    flux=flux,
                    target_lock=target_lock,
                    terminal_mode=terminal_mode,
                    defender_pressure=defender_pressure,
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
                            plugin_module.on_event(
                                {
                                    "type": "defense_action",
                                    "action": defense_action,
                                    "target": target_lock,
                                    "t": visual_t,
                                }
                            )
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

            log_budget = update_logs(
                logs,
                level,
                visual_t,
                beat,
                max_items=max(12, int(height * compute_quality_scale(args.quality_mode, dropped_frames))),
                speed_factor=speed_factor,
                budget=log_budget,
                incident_feed=incident_feed,
            )

            quality_scale = compute_quality_scale(args.quality_mode, dropped_frames)

            if plugin_module is not None and hasattr(plugin_module, "on_frame_context"):
                try:
                    context_update = plugin_module.on_frame_context(
                        {
                            "level": level,
                            "flux": flux,
                            "beat": beat,
                            "mission_phase": mission_phase_name,
                            "mission_objective": mission_objective,
                            "defender_state": defender_state,
                            "module_levels": dict(module_levels),
                            "target_lock": target_lock,
                            "operation_mode": operation_mode,
                        }
                    )
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

            audio_t = idx * frame_time  # real playback position, not speed-scaled
            frame = render_frame(
                width=width,
                height=height,
                level=level,
                t=audio_t,
                duration=audio.duration,
                logs=logs,
                history=history,
                pulse=pulse,
                speed_factor=speed_factor,
                bands=bands,
                sensitivity=sensitivity,
                theme_name=theme_name,
                terminal_mode=terminal_mode,
                switch_min=args.terminal_switch_min,
                switch_max=args.terminal_switch_max,
                operation_mode=operation_mode,
                target_lock=target_lock,
                net_state=net_state,
                shell_lines=shell_lines,
                daemon=daemon,
                clearance=clearance,
                open_ports=open_ports,
                trace_hops=trace_hops,
                packet=packet,
                flux=flux,
                mission_phase=mission_phase_name,
                mission_objective=mission_objective,
                defender_state=defender_state,
                glitch_frames=glitch_frames,
                scanline_flash=scanline_flash,
                jitter=jitter,
                banner_text=banner_text,
                banner_align=banner_align,
                banner_anim=banner_anim,
                banner_size=banner_size,
                show_banner=show_banner,
                quality_scale=quality_scale,
                keys_line=keys_line,
                module_levels=module_levels,
                visual_state=visual_state,
                ui_style=args.ui_style,
            )

            sys.stdout.write("\033[H\033[J")
            sys.stdout.write(frame)
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
        sys.stdout.write(SHOW_CURSOR + RESET + "\n")
        sys.stdout.flush()
        if rec is not None:
            rec.close()
        if args.video_hook and args.record_file:
            env = os.environ.copy()
            env["CMD_AUDIO_RECORD_FILE"] = args.record_file
            try:
                subprocess.run(args.video_hook, shell=True, env=env, check=False)
            except Exception as exc:
                print(f"Video hook error: {exc}", file=sys.stderr)
        if player and player.poll() is None:
            player.terminate()
        if cleanup_wav:
            try:
                os.unlink(wav_input)
            except OSError:
                pass
        close_live_ui()

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
