"""
Base plugin interfaces for StrataRegula.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol
from enum import Enum


@dataclass
class PluginInfo:
    """Plugin metadata information."""
    name: str
    version: str
    description: str
    author: str = ""
    category: str = ""
    priority: int = 0


class PatternPlugin(Protocol):
    """Protocol for pattern expansion plugins."""
    
    @property
    def info(self) -> PluginInfo:
        """Get plugin metadata."""
        ...
    
    def can_handle(self, pattern: str) -> bool:
        """Check if this plugin can handle the given pattern."""
        ...
    
    def expand(self, pattern: str, context: Dict[str, Any]) -> List[str]:
        """Expand the pattern with the given context."""
        ...


class PluginManager(ABC):
    """Base plugin manager interface."""
    
    @abstractmethod
    def register_plugin(self, plugin: PatternPlugin) -> None:
        """Register a plugin."""
        pass
    
    @abstractmethod
    def get_plugins(self) -> List[PatternPlugin]:
        """Get all registered plugins."""
        pass
    
    @abstractmethod
    def expand_pattern(self, pattern: str, context: Dict[str, Any]) -> List[str]:
        """Expand a pattern using available plugins."""
        pass