"""
Built-in simulation plugins for StrataRegula.
"""

from .base import PatternPlugin, PluginInfo


class SimulationPlugins:
    """Container for built-in simulation plugins."""
    
    @staticmethod
    def get_all_plugins():
        """Get all built-in simulation plugins."""
        return []