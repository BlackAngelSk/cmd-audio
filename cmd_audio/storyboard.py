"""Scene graph / storyboard system (Phase 5.4)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class StoryboardScene:
    """A single scene in a storyboard."""
    name: str
    scene_type: str  # "hacker", "waveform", "spectrogram", etc.
    duration: float = 5.0
    transition: str = "none"  # "none", "crossfade", "cut"
    transition_duration: float = 1.0
    theme: str = ""
    visual_module: str = ""
    audio_fx: str = ""
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Storyboard:
    """A storyboard with scenes and transitions."""
    name: str
    scenes: List[StoryboardScene] = field(default_factory=list)
    loop: bool = True
    current_scene_idx: int = 0

    def add_scene(self, scene: StoryboardScene) -> None:
        self.scenes.append(scene)

    def get_current_scene(self) -> Optional[StoryboardScene]:
        if 0 <= self.current_scene_idx < len(self.scenes):
            return self.scenes[self.current_scene_idx]
        return None

    def advance_scene(self) -> bool:
        if self.current_scene_idx < len(self.scenes) - 1:
            self.current_scene_idx += 1
            return True
        elif self.loop:
            self.current_scene_idx = 0
            return True
        return False

    def reset(self) -> None:
        self.current_scene_idx = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "scenes": [
                {
                    "name": s.name,
                    "scene_type": s.scene_type,
                    "duration": s.duration,
                    "transition": s.transition,
                    "transition_duration": s.transition_duration,
                    "theme": s.theme,
                    "visual_module": s.visual_module,
                    "audio_fx": s.audio_fx,
                    "params": s.params,
                }
                for s in self.scenes
            ],
            "loop": self.loop,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Storyboard":
        scenes = []
        for s in data.get("scenes", []):
            scenes.append(StoryboardScene(
                name=s.get("name", ""),
                scene_type=s.get("scene_type", "hacker"),
                duration=s.get("duration", 5.0),
                transition=s.get("transition", "none"),
                transition_duration=s.get("transition_duration", 1.0),
                theme=s.get("theme", ""),
                visual_module=s.get("visual_module", ""),
                audio_fx=s.get("audio_fx", ""),
                params=s.get("params", {}),
            ))
        return cls(
            name=data.get("name", ""),
            scenes=scenes,
            loop=data.get("loop", True),
        )


def load_storyboard(path: str) -> Storyboard:
    """Load a storyboard from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Storyboard.from_dict(data)


def save_storyboard(storyboard: Storyboard, path: str) -> None:
    """Save a storyboard to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(storyboard.to_dict(), f, indent=2)


def create_default_storyboard() -> Storyboard:
    """Create a default storyboard with a few scenes."""
    sb = Storyboard(name="Default")
    sb.add_scene(StoryboardScene(name="Intro", scene_type="hacker", duration=10.0))
    sb.add_scene(StoryboardScene(name="Main", scene_type="waveform", duration=30.0))
    sb.add_scene(StoryboardScene(name="Climax", scene_type="spectrogram", duration=10.0))
    return sb