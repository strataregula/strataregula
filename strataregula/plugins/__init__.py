"""
Advanced Plugin System for Strataregula - Layered Configuration Management.

This plugin system provides:
- Automatic plugin discovery via entry points and filesystem scanning
- Lifecycle management with states (discovered, loaded, active, failed)
- Configuration management with YAML/JSON support
- Error handling with circuit breakers and fallback mechanisms
- Hook integration for extensibility
"""

# Core plugin interfaces
from .base import PatternPlugin, PluginInfo, PluginManager

# Built-in plugins - not available in v0.3.0
# from .builtin import SimulationPlugins
from .config import (
    ConfigValidator,
    GlobalPluginConfig,
    JSONSchemaValidator,
    PluginConfigEntry,
    PluginConfigManager,
)
from .error_handling import (
    CircuitBreaker,
    ErrorCategory,
    ErrorRecoveryStrategy,
    ErrorSeverity,
    FallbackHandler,
    PluginError,
    PluginErrorHandler,
)

# Advanced plugin system components
from .loader import PluginEntryPoint, PluginLoader, PluginLoadResult
from .manager import EnhancedPluginManager, PluginConfig, PluginContext, PluginState

__all__ = [
    "CircuitBreaker",
    "ConfigValidator",
    "EnhancedPluginManager",
    "ErrorCategory",
    "ErrorRecoveryStrategy",
    "ErrorSeverity",
    "FallbackHandler",
    "GlobalPluginConfig",
    "JSONSchemaValidator",
    # Core interfaces
    "PatternPlugin",
    "PluginConfig",
    "PluginConfigEntry",
    # Configuration
    "PluginConfigManager",
    "PluginContext",
    "PluginEntryPoint",
    "PluginError",
    # Error handling
    "PluginErrorHandler",
    "PluginInfo",
    "PluginLoadResult",
    # Advanced system
    "PluginLoader",
    "PluginManager",
    "PluginState",
    # Built-in
    "SimulationPlugins",
]
