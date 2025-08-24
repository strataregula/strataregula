"""
Built-in plugins for general simulation scenarios.
Simplified from the original enterprise plugins.
"""

import re
import os
from typing import Dict, Any, List
from .base import PatternPlugin, PluginInfo


class RegionPlugin(PatternPlugin):
    """Plugin for expanding region-based patterns."""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="RegionPlugin",
            version="1.0.0",
            description="Expands patterns with Japanese prefectures/regions"
        )
    
    def can_handle(self, pattern: str) -> bool:
        return "*" in pattern and ("region" in pattern.lower() or "prefecture" in pattern.lower())
    
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Expand pattern with Japanese prefectures."""
        prefectures = context.get('data_sources', {}).get('prefectures', [
            'hokkaido', 'aomori', 'iwate', 'miyagi', 'akita', 'yamagata', 'fukushima',
            'ibaraki', 'tochigi', 'gunma', 'saitama', 'chiba', 'tokyo', 'kanagawa',
            'niigata', 'toyama', 'ishikawa', 'fukui', 'yamanashi', 'nagano',
            'gifu', 'shizuoka', 'aichi', 'mie', 'shiga', 'kyoto', 'osaka',
            'hyogo', 'nara', 'wakayama', 'tottori', 'shimane', 'okayama', 'hiroshima',
            'yamaguchi', 'tokushima', 'kagawa', 'ehime', 'kochi', 'fukuoka',
            'saga', 'nagasaki', 'kumamoto', 'oita', 'miyazaki', 'kagoshima', 'okinawa'
        ])
        
        result = {}
        value = context.get('value', 0)
        
        for prefecture in prefectures:
            expanded = pattern.replace('*', prefecture)
            result[expanded] = value
        
        return result


class SimulationPlugin(PatternPlugin):
    """Plugin for general simulation pattern expansion."""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="SimulationPlugin", 
            version="1.0.0",
            description="Expands general simulation patterns for various scenarios"
        )
    
    def can_handle(self, pattern: str) -> bool:
        simulation_keywords = ['simulation', 'scenario', 'model', 'test', 'demo']
        return "*" in pattern and any(keyword in pattern.lower() for keyword in simulation_keywords)
    
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Expand simulation patterns."""
        simulation_types = ['basic', 'advanced', 'custom', 'production']
        result = {}
        value = context.get('value', 0)
        
        for level in simulation_types:
            expanded = pattern.replace('*', level)
            result[expanded] = value
            
        return result


class ProcessPlugin(PatternPlugin):
    """Plugin for process pattern expansion."""
    
    @property 
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="ProcessPlugin",
            version="1.0.0", 
            description="Expands process patterns for workflow simulations"
        )
    
    def can_handle(self, pattern: str) -> bool:
        process_keywords = ['process', 'workflow', 'step', 'stage', 'phase']
        return "*" in pattern and any(keyword in pattern.lower() for keyword in process_keywords)
    
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Expand process patterns."""
        process_stages = ['start', 'process', 'review', 'complete']
        result = {}
        value = context.get('value', 0)
        
        for stage in process_stages:
            expanded = pattern.replace('*', stage)
            result[expanded] = value
            
        return result


class ResourcePlugin(PatternPlugin):
    """Plugin for resource allocation pattern expansion."""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="ResourcePlugin",
            version="1.0.0",
            description="Expands resource allocation patterns for infrastructure"
        )
    
    def can_handle(self, pattern: str) -> bool:
        resource_keywords = ['cpu', 'memory', 'storage', 'network', 'resource']
        return "*" in pattern and any(keyword in pattern.lower() for keyword in resource_keywords)
    
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Expand resource patterns."""
        resource_sizes = ['xs', 's', 'm', 'l', 'xl']
        result = {}
        value = context.get('value', 0)
        
        for size in resource_sizes:
            expanded = pattern.replace('*', size)
            result[expanded] = value
            
        return result


class EnvironmentPlugin(PatternPlugin):
    """Plugin for environment-based pattern expansion."""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="EnvironmentPlugin",
            version="1.0.0",
            description="Expands environment-specific patterns"
        )
    
    def can_handle(self, pattern: str) -> bool:
        env_keywords = ['env', 'environment', 'stage']
        return "*" in pattern and any(keyword in pattern.lower() for keyword in env_keywords)
    
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Expand environment patterns."""
        environments = ['dev', 'staging', 'prod', 'dr']
        result = {}
        value = context.get('value', 0)
        
        for env in environments:
            expanded = pattern.replace('*', env)
            result[expanded] = value
            
        return result


class SimulationPlugins:
    """Collection of general simulation plugins."""
    
    @staticmethod
    def get_all_plugins() -> List[PatternPlugin]:
        """Get all simulation plugins."""
        return [
            RegionPlugin(),
            SimulationPlugin(), 
            ProcessPlugin(),
            ResourcePlugin(),
            EnvironmentPlugin()
        ]
    
    @staticmethod
    def register_all(plugin_manager) -> None:
        """Register all simulation plugins with a plugin manager."""
        for plugin in SimulationPlugins.get_all_plugins():
            plugin_manager.register_plugin(plugin)