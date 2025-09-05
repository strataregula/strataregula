"""
Base Plugin Infrastructure for StrataRegula

This module provides base classes and interfaces for the plugin system.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """Plugin metadata and information."""

    name: str
    version: str
    description: str
    author: Optional[str] = None
    requires: Optional[List[str]] = None
    category: str = "general"


class PatternPlugin(ABC):
    """Base class for pattern processing plugins."""

    def __init__(self, info: PluginInfo):
        self.info = info
        self.logger = logging.getLogger(f"{__name__}.{info.name}")

    @abstractmethod
    async def process(self, pattern: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a pattern with given data."""
        pass

    def initialize(self) -> bool:
        """Initialize the plugin."""
        return True

    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        # Default implementation does nothing
        # Subclasses can override if cleanup is needed
        return


class PluginManager:
    """Simple plugin manager for v0.3.0 compatibility."""

    def __init__(self):
        self.plugins: Dict[str, PatternPlugin] = {}
        self.logger = logging.getLogger(f"{__name__}.PluginManager")

    def register_plugin(self, plugin: PatternPlugin) -> bool:
        """Register a plugin."""
        try:
            if plugin.initialize():
                self.plugins[plugin.info.name] = plugin
                self.logger.info(f"Registered plugin: {plugin.info.name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to register plugin {plugin.info.name}: {e}")
            return False

    def get_plugin(self, name: str) -> Optional[PatternPlugin]:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self.plugins.keys())
