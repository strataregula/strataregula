"""
Simple plugin base classes for YAML Config Compiler.
Simplified from the original complex plugin system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """Simple plugin information."""
    name: str
    version: str
    description: str


class PatternPlugin(ABC):
    """Base class for pattern expansion plugins."""
    
    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """Return plugin information."""
        pass
    
    @abstractmethod
    def can_handle(self, pattern: str) -> bool:
        """Check if this plugin can handle the given pattern."""
        pass
    
    @abstractmethod
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Expand the pattern with the given context."""
        pass


class PluginManager:
    """Simple plugin manager."""
    
    def __init__(self):
        self.plugins: List[PatternPlugin] = []
    
    def register_plugin(self, plugin: PatternPlugin) -> None:
        """Register a plugin."""
        self.plugins.append(plugin)
        logger.info(f"Registered plugin: {plugin.info.name}")
    
    def unregister_plugin(self, plugin: PatternPlugin) -> None:
        """Unregister a plugin."""
        if plugin in self.plugins:
            self.plugins.remove(plugin)
            logger.info(f"Unregistered plugin: {plugin.info.name}")
    
    def get_plugin_for_pattern(self, pattern: str) -> Optional[PatternPlugin]:
        """Find the first plugin that can handle the given pattern."""
        for plugin in self.plugins:
            if plugin.can_handle(pattern):
                return plugin
        return None
    
    def expand_pattern(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Expand pattern using appropriate plugin."""
        plugin = self.get_plugin_for_pattern(pattern)
        if plugin:
            return plugin.expand(pattern, context)
        return {pattern: context.get('value', None)}
    
    def list_plugins(self) -> List[PluginInfo]:
        """List all registered plugins."""
        return [plugin.info for plugin in self.plugins]