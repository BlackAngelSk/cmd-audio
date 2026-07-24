"""Plugin marketplace (Phase 4.10)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)

MARKETPLACE_DIR = os.path.expanduser("~/.config/cmd-audio/plugins")


@dataclass
class PluginVersion:
    version: str
    file: str
    hash: str = ""


@dataclass
class PluginManifest:
    name: str
    description: str
    author: str
    versions: List[PluginVersion] = field(default_factory=list)
    installed: bool = False


class PluginMarketplace:
    """Manage plugins from a local or remote registry."""

    def __init__(self, registry_url: str = "") -> None:
        self.registry_url = registry_url
        self.plugins: Dict[str, PluginManifest] = {}

    def list_plugins(self) -> List[PluginManifest]:
        return list(self.plugins.values())

    def search(self, query: str) -> List[PluginManifest]:
        return [p for p in self.plugins.values() if query.lower() in p.name.lower() or query.lower() in p.description.lower()]

    def install(self, name: str, path: str) -> bool:
        if name not in self.plugins:
            manifest = PluginManifest(name=name, description="", author="", installed=False)
            self.plugins[name] = manifest
        self.plugins[name].installed = True
        self.plugins[name].versions.append(PluginVersion(version="0.1.0", file=path))
        logger.info("Installed plugin %s from %s", name, path)
        return True

    def uninstall(self, name: str) -> bool:
        if name in self.plugins:
            self.plugins[name].installed = False
            logger.info("Uninstalled plugin %s", name)
            return True
        return False


def create_marketplace(registry_url: str = "") -> PluginMarketplace:
    return PluginMarketplace(registry_url)