"""Formal plugin API with event system (Phase 4.6)."""

from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PluginInfo:
    """Metadata about a loaded plugin."""
    name: str
    version: str = "0.1.0"
    author: str = ""
    description: str = ""
    module: Any = None
    enabled: bool = True


class PluginRegistry:
    """Registry for managing plugins with event system."""

    def __init__(self) -> None:
        self.plugins: Dict[str, PluginInfo] = {}
        self._events: Dict[str, List[Callable[..., Any]]] = {}
        self._enabled_events: Dict[str, bool] = {}

    def register_plugin(self, name: str, path: str) -> bool:
        """Register a plugin from a Python file."""
        if not os.path.exists(path):
            logger.error("Plugin file not found: %s", path)
            return False
        try:
            mod_name = f"cmd_audio_plugin_{abs(hash(path))}"
            spec = importlib.util.spec_from_file_location(mod_name, path)
            if spec is None or spec.loader is None:
                logger.error("Could not load plugin spec: %s", path)
                return False
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            info = PluginInfo(
                name=name,
                version=str(getattr(module, "PLUGIN_VERSION", "0.1.0")),
                author=str(getattr(module, "PLUGIN_AUTHOR", "")),
                description=str(getattr(module, "PLUGIN_DESCRIPTION", "")),
                module=module,
            )
            self.plugins[name] = info
            logger.info("Registered plugin: %s", name)
            return True
        except Exception as exc:
            logger.error("Failed to register plugin %s: %s", name, exc)
            return False

    def unregister_plugin(self, name: str) -> None:
        if name in self.plugins:
            del self.plugins[name]
            logger.info("Unregistered plugin: %s", name)

    def on(self, event: str, handler: Callable[..., Any]) -> None:
        """Subscribe to an event."""
        if event not in self._events:
            self._events[event] = []
        self._events[event].append(handler)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Emit an event to all registered handlers."""
        for handler in self._events.get(event, []):
            try:
                handler(*args, **kwargs)
            except Exception as exc:
                logger.error("Plugin event handler error for %s: %s", event, exc)

    def list_plugins(self) -> List[PluginInfo]:
        return list(self.plugins.values())

    def is_loaded(self, name: str) -> bool:
        return name in self.plugins


def load_plugin(path: str, name: str = "") -> Optional[PluginInfo]:
    """Convenience function to load a plugin."""
    registry = PluginRegistry()
    plugin_name = name or os.path.basename(path).replace(".py", "")
    if registry.register_plugin(plugin_name, path):
        return registry.plugins[plugin_name]
    return None