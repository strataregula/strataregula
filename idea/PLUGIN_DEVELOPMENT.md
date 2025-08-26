# Strataregula Plugin Development Guide

## 🚀 Getting Started

This guide will walk you through creating custom plugins for the Strataregula layered configuration management system.

### What are Plugins?

Plugins in Strataregula extend the pattern expansion capabilities, allowing you to:
- Add custom pattern matching logic
- Implement domain-specific expansion rules
- Integrate with external data sources
- Create specialized configuration generators

### Plugin Architecture Overview

```
┌─────────────────┐
│   PluginLoader  │ ← Discovers and loads plugins
└─────────────────┘
         │
┌─────────────────┐
│ PluginManager   │ ← Manages plugin lifecycle
└─────────────────┘
         │
┌─────────────────┐
│  PatternPlugin  │ ← Your custom plugin
└─────────────────┘
```

## 📋 Plugin Interface

All plugins must inherit from the `PatternPlugin` base class:

```python
from strataregula.plugins.base import PatternPlugin, PluginInfo
from typing import Dict, Any

class MyPlugin(PatternPlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="my-plugin",
            version="1.0.0",
            description="My custom pattern plugin"
        )
    
    def can_handle(self, pattern: str) -> bool:
        """Return True if this plugin can handle the pattern."""
        return pattern.startswith('my:')
    
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Expand the pattern with the given context."""
        # Your expansion logic here
        return {pattern.replace('my:', ''): context.get('value')}
```

## 🏗️ Creating Your First Plugin

### Step 1: Project Setup

Create a new Python file for your plugin:

```bash
mkdir my_strataregula_plugin
cd my_strataregula_plugin
touch timestamp_plugin.py
touch __init__.py
```

### Step 2: Implement the Plugin

```python
# timestamp_plugin.py
import datetime
from strataregula.plugins.base import PatternPlugin, PluginInfo
from typing import Dict, Any

class TimestampPlugin(PatternPlugin):
    """Plugin that adds timestamps to configuration patterns."""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="timestamp-plugin",
            version="1.0.0", 
            description="Adds timestamp expansion to patterns"
        )
    
    def can_handle(self, pattern: str) -> bool:
        """Handle patterns containing @timestamp."""
        return '@timestamp' in pattern
    
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Replace @timestamp with current timestamp."""
        timestamp_format = context.get('timestamp_format', '%Y%m%d_%H%M%S')
        current_time = datetime.datetime.now()
        timestamp_str = current_time.strftime(timestamp_format)
        
        # Replace @timestamp in pattern
        expanded_pattern = pattern.replace('@timestamp', timestamp_str)
        
        return {expanded_pattern: context.get('value')}
```

### Step 3: Test Your Plugin

```python
# test_timestamp_plugin.py
from timestamp_plugin import TimestampPlugin

def test_timestamp_plugin():
    plugin = TimestampPlugin()
    
    # Test pattern detection
    assert plugin.can_handle('service.@timestamp.config')
    assert not plugin.can_handle('service.normal.config')
    
    # Test expansion
    context = {'value': 'test_value', 'timestamp_format': '%Y%m%d'}
    result = plugin.expand('service.@timestamp.config', context)
    
    # Result should have timestamp instead of @timestamp
    pattern = list(result.keys())[0]
    assert '@timestamp' not in pattern
    assert 'service.' in pattern
    assert '.config' in pattern
    print(f"Expanded pattern: {pattern}")

if __name__ == '__main__':
    test_timestamp_plugin()
```

## 🔧 Advanced Plugin Features

### Configuration Support

Plugins can access configuration through the context:

```python
class ConfigurablePlugin(PatternPlugin):
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Access plugin-specific configuration
        plugin_config = context.get('plugin_settings', {})
        custom_prefix = plugin_config.get('prefix', 'default')
        
        return {f"{custom_prefix}.{pattern}": context.get('value')}
```

### Hook Integration

Plugins can register hooks for lifecycle events:

```python
from strataregula.hooks.base import HookManager

class HookAwarePlugin(PatternPlugin):
    def register_hooks(self, hook_manager: HookManager):
        """Register plugin hooks."""
        hook_manager.register(
            'pre_expand',
            self._pre_expand_hook,
            priority=10
        )
    
    async def _pre_expand_hook(self, pattern: str, context: Dict[str, Any]):
        """Pre-expansion hook."""
        print(f"About to expand pattern: {pattern}")
```

### Error Handling

Implement robust error handling:

```python
class RobustPlugin(PatternPlugin):
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Your expansion logic
            return self._perform_expansion(pattern, context)
        except ValueError as e:
            # Handle validation errors
            return {pattern: f"ERROR: {e}"}
        except Exception as e:
            # Handle unexpected errors
            import logging
            logging.error(f"Plugin error: {e}")
            return {pattern: context.get('value', 'ERROR')}
```

## 📦 Plugin Distribution

### Method 1: Entry Points (Recommended)

Create a `setup.py` or `pyproject.toml` for distribution:

```toml
# pyproject.toml
[build-system]
requires = ["setuptools", "wheel"]

[project]
name = "my-strataregula-plugin"
version = "1.0.0"
description = "Custom Strataregula plugin"

[project.entry-points."strataregula.plugins"]
timestamp = "my_strataregula_plugin.timestamp_plugin:TimestampPlugin"
```

Install your plugin:
```bash
pip install -e .
```

### Method 2: Local Plugin Directory

Place your plugin in a standard location:

```bash
# User plugins
~/.strataregula/plugins/my_plugin.py

# Project plugins  
./plugins/my_plugin.py

# System plugins
/etc/strataregula/plugins/my_plugin.py
```

## 🧪 Testing Plugins

### Unit Testing

```python
import pytest
from your_plugin import YourPlugin

class TestYourPlugin:
    def setup_method(self):
        self.plugin = YourPlugin()
    
    def test_can_handle(self):
        assert self.plugin.can_handle('valid:pattern')
        assert not self.plugin.can_handle('invalid:pattern')
    
    def test_expand(self):
        context = {'value': 'test'}
        result = self.plugin.expand('valid:pattern', context)
        assert isinstance(result, dict)
        assert len(result) > 0
    
    def test_plugin_info(self):
        info = self.plugin.info
        assert info.name
        assert info.version
        assert info.description
```

### Integration Testing

```python
from strataregula.plugins.manager import EnhancedPluginManager
from strataregula.plugins.config import PluginConfigManager

def test_plugin_integration():
    # Setup plugin manager
    config_manager = PluginConfigManager()
    plugin_manager = EnhancedPluginManager(
        config=config_manager.get_global_config()
    )
    
    # Discover and load plugins
    plugins = plugin_manager.discover_plugins()
    assert 'your-plugin' in plugins
    
    # Test pattern expansion
    result = plugin_manager.expand_pattern(
        'your:test:pattern', 
        {'value': 'test_value'}
    )
    assert 'your:test:pattern' in str(result)
```

## 🔍 Debugging Plugins

### Logging

Use structured logging for debugging:

```python
import logging

logger = logging.getLogger(__name__)

class DebuggablePlugin(PatternPlugin):
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"Expanding pattern: {pattern}")
        logger.debug(f"Context keys: {list(context.keys())}")
        
        result = self._do_expansion(pattern, context)
        
        logger.debug(f"Expansion result: {result}")
        return result
```

### Plugin Inspector

Check plugin status programmatically:

```python
from strataregula.plugins.manager import EnhancedPluginManager

manager = EnhancedPluginManager()
stats = manager.get_plugin_stats()

print("Plugin Statistics:")
print(f"Total: {stats['total_plugins']}")
print(f"Active: {stats['by_state']['active']}")
print(f"Failed: {stats['by_state']['failed']}")
```

## 📚 Plugin Examples

### 1. Environment Variable Plugin

```python
import os

class EnvVarPlugin(PatternPlugin):
    @property 
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="env-var-plugin",
            version="1.0.0",
            description="Expands environment variables"
        )
    
    def can_handle(self, pattern: str) -> bool:
        return pattern.startswith('$')
    
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        env_var = pattern[1:]  # Remove $ prefix
        value = os.getenv(env_var, context.get('value', ''))
        return {pattern: value}
```

### 2. Database Plugin

```python
import sqlite3

class DatabasePlugin(PatternPlugin):
    def __init__(self):
        self.db_path = None
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="database-plugin",
            version="1.0.0",
            description="Expands patterns from database"
        )
    
    def can_handle(self, pattern: str) -> bool:
        return pattern.startswith('db:')
    
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Extract table and column from pattern: db:table:column
        parts = pattern.split(':')
        if len(parts) != 3:
            return {pattern: context.get('value')}
        
        _, table, column = parts
        
        try:
            conn = sqlite3.connect(self._get_db_path(context))
            cursor = conn.execute(f"SELECT {column} FROM {table}")
            results = {}
            
            for i, row in enumerate(cursor.fetchall()):
                results[f"{table}.{column}.{i}"] = row[0]
            
            conn.close()
            return results
            
        except Exception as e:
            return {pattern: f"ERROR: {e}"}
    
    def _get_db_path(self, context: Dict[str, Any]) -> str:
        return context.get('db_path', 'config.db')
```

### 3. Template Plugin

```python
from jinja2 import Template

class TemplatePlugin(PatternPlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="template-plugin",
            version="1.0.0",
            description="Jinja2 template expansion"
        )
    
    def can_handle(self, pattern: str) -> bool:
        return '{{' in pattern and '}}' in pattern
    
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            template = Template(pattern)
            rendered = template.render(**context)
            return {rendered: context.get('value')}
        except Exception as e:
            return {pattern: f"TEMPLATE_ERROR: {e}"}
```

## 🔧 Plugin Configuration

### Plugin-specific Configuration

```yaml
# ~/.strataregula/plugins.yaml
global:
  auto_discover: true
  lazy_loading: false

plugins:
  timestamp-plugin:
    enabled: true
    priority: 10
    settings:
      default_format: "%Y-%m-%d_%H:%M:%S"
      timezone: "UTC"
  
  database-plugin:
    enabled: true
    priority: 20
    settings:
      db_path: "/path/to/config.db"
      timeout: 30
    dependencies:
      - "timestamp-plugin"
```

### Configuration in Plugin

```python
class ConfigurablePlugin(PatternPlugin):
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Access plugin settings from context
        settings = context.get('plugin_settings', {})
        
        # Use configuration values
        custom_format = settings.get('format', 'default_format')
        timeout = settings.get('timeout', 30)
        
        # Implement expansion logic with configuration
        return self._expand_with_config(pattern, context, custom_format, timeout)
```

## 🚀 Best Practices

### 1. Plugin Design
- ✅ Keep plugins focused on single responsibilities
- ✅ Use descriptive plugin names and clear documentation  
- ✅ Implement proper error handling and fallbacks
- ✅ Validate input patterns and context data
- ✅ Support configuration through settings

### 2. Performance
- ✅ Cache expensive operations
- ✅ Use lazy loading for heavy resources
- ✅ Implement timeouts for external calls
- ✅ Monitor memory usage in long-running plugins

### 3. Error Handling
- ✅ Gracefully handle missing dependencies
- ✅ Provide meaningful error messages
- ✅ Implement circuit breakers for unreliable services
- ✅ Use structured logging for debugging

### 4. Testing
- ✅ Write comprehensive unit tests
- ✅ Test error conditions and edge cases
- ✅ Include integration tests with the plugin system
- ✅ Test configuration scenarios

### 5. Documentation
- ✅ Document pattern formats your plugin handles
- ✅ Provide usage examples
- ✅ Document configuration options
- ✅ Include troubleshooting guides

## 📖 API Reference

### Core Classes

#### `PatternPlugin`
Base class for all plugins.

**Methods:**
- `info: PluginInfo` - Plugin metadata
- `can_handle(pattern: str) -> bool` - Pattern compatibility check
- `expand(pattern: str, context: Dict[str, Any]) -> Dict[str, Any]` - Pattern expansion

#### `PluginInfo`  
Plugin metadata container.

**Fields:**
- `name: str` - Plugin name
- `version: str` - Plugin version
- `description: str` - Plugin description

#### `EnhancedPluginManager`
Main plugin management system.

**Methods:**
- `discover_plugins() -> List[str]` - Find available plugins
- `load_plugin(name: str) -> bool` - Load specific plugin
- `activate_plugin(name: str) -> bool` - Activate loaded plugin
- `expand_pattern(pattern: str, context: Dict[str, Any]) -> Dict[str, Any]` - Expand using plugins

### Configuration Classes

#### `PluginConfigManager`
Manages plugin configurations.

**Methods:**
- `get_plugin_config(name: str) -> PluginConfigEntry` - Get plugin config
- `is_plugin_enabled(name: str) -> bool` - Check if enabled
- `get_plugin_settings(name: str) -> Dict[str, Any]` - Get plugin settings

## 🤝 Contributing Plugins

### Submitting Plugins

1. **Create** a well-tested plugin following this guide
2. **Document** your plugin with examples
3. **Test** integration with the plugin system  
4. **Submit** a pull request to the main repository

### Plugin Registry

Popular community plugins will be featured in the official plugin registry at:
https://github.com/strataregula/plugins

---

## 📞 Support

Need help developing plugins?

- 📚 **Documentation**: https://docs.strataregula.com
- 🐛 **Issues**: https://github.com/strataregula/strataregula/issues
- 💬 **Discussions**: https://github.com/strataregula/strataregula/discussions
- 📧 **Email**: plugins@strataregula.com

Happy plugin development! 🚀