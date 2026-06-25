"""Mission timeline progression and defender countermeasure AI."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from cmd_audio.config import (
    DEFENDER_ACTIONS,
    MISSION_PHASES,
    OPERATION_MODES,
    TARGETS,
)
from cmd_audio.visual import generate_shell_feed
from cmd_audio.utils import clamp


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