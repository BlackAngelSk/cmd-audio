"""Scene pack browser (Phase 3.6)."""

from __future__ import annotations

import os
import pickle
import json
from typing import Dict, List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)

SCENE_PACK_DIR = os.path.expanduser("~/.config/cmd-audio/scene_packs")


def ensure_scene_pack_dir() -> None:
    os.makedirs(SCENE_PACK_DIR, exist_ok=True)


def list_scene_packs() -> List[str]:
    ensure_scene_pack_dir()
    try:
        return [f[:-5] for f in os.listdir(SCENE_PACK_DIR) if f.endswith(".json")]
    except FileNotFoundError:
        return []


def load_scene_pack(name: str) -> Dict:
    path = os.path.join(SCENE_PACK_DIR, f"{name}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.error("Failed to load scene pack %s: %s", name, exc)
        return {}


def save_scene_pack(name: str, pack: Dict) -> None:
    ensure_scene_pack_dir()
    path = os.path.join(SCENE_PACK_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pack, f, indent=2)
    logger.info("Saved scene pack: %s", path)


def get_scene_pack_info(name: str) -> Optional[Dict]:
    pack = load_scene_pack(name)
    if not pack:
        return None
    return {
        "name": name,
        "modules": pack.get("modules", []),
        "scenes": len(pack.get("scenes", [])),
        "duration": pack.get("duration", 0),
    }


def preview_scene_pack(name: str, width: int = 60, height: int = 20) -> List[str]:
    """Generate a preview of a scene pack."""
    pack = load_scene_pack(name)
    lines = [f"Scene Pack: {name}"]
    lines.append("=" * min(width, 40))
    modules = pack.get("modules", [])
    lines.append(f"Modules: {', '.join(modules) if modules else 'none'}")
    scenes = pack.get("scenes", [])
    if scenes:
        for i, s in enumerate(scenes[:height - 5]):
            lines.append(f"  [{i + 1}] {s.get('name', 'unnamed')} ({s.get('duration', '?')}s)")
    else:
        lines.append("  (no scenes)")
    return lines