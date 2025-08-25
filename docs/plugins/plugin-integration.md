# Plugin Integration Guide

This guide shows how to integrate plugins with the Strataregula ecosystem.

## Plugin Discovery

Strataregula uses Python entry points for automatic plugin discovery. Plugins are registered in `pyproject.toml`:

```toml
[project.entry-points."strataregula.plugins"]
"plugin-name" = "package.module:PluginClass"
```

### Example Entry Point Registration

```toml
[project.entry-points."strataregula.plugins"]
"doe_runner" = "strataregula_doe_runner.plugin:DOERunnerPlugin"
"restaurant_config" = "strataregula_restaurant_config.plugin:RestaurantConfigPlugin"
```

## Plugin Discovery API

### Automatic Discovery

```python
import pkg_resources

def discover_plugins():
    """Discover all registered Strataregula plugins."""
    plugins = {}
    
    for entry_point in pkg_resources.iter_entry_points('strataregula.plugins'):
        try:
            plugin_class = entry_point.load()
            plugin = plugin_class()
            plugins[entry_point.name] = plugin
        except Exception as e:
            print(f"Failed to load plugin {entry_point.name}: {e}")
    
    return plugins
```

### Manual Plugin Loading

```python
from strataregula_doe_runner.plugin import DOERunnerPlugin

# Direct instantiation
plugin = DOERunnerPlugin()

# Get plugin information
info = plugin.get_info()
print(f"Loaded plugin: {info['name']} v{info['version']}")
```

## Plugin Usage Patterns

### Command Execution

```python
# Get available plugins
plugins = discover_plugins()

# Execute plugin command
if 'doe_runner' in plugins:
    plugin = plugins['doe_runner']
    
    result = plugin.execute_cases(
        cases_path="cases.csv",
        metrics_path="metrics.csv",
        max_workers=4
    )
    
    if result['status'] == 'success':
        print(f"Execution completed: {result['stats']}")
    else:
        print(f"Execution failed: {result['message']}")
```

### Plugin Information

```python
def list_plugins():
    """List all available plugins with their capabilities."""
    plugins = discover_plugins()
    
    for name, plugin in plugins.items():
        info = plugin.get_info()
        print(f"\nPlugin: {info['name']} v{info['version']}")
        print(f"Description: {info['description']}")
        print(f"Author: {info.get('author', 'Unknown')}")
        
        if 'supported_commands' in info:
            print("Commands:")
            for cmd in info['supported_commands']:
                print(f"  - {cmd}")
```

### Error Handling

```python
def safe_plugin_execution(plugin, command, **kwargs):
    """Safely execute plugin command with error handling."""
    try:
        method = getattr(plugin, command, None)
        if not method:
            return {
                'status': 'error',
                'message': f'Command {command} not supported'
            }
        
        return method(**kwargs)
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Plugin execution failed: {str(e)}'
        }
```

## Configuration Management

### Plugin-Specific Configuration

```python
import yaml
from pathlib import Path

class PluginConfigManager:
    def __init__(self, config_dir: str = "~/.strataregula"):
        self.config_dir = Path(config_dir).expanduser()
        self.config_dir.mkdir(exist_ok=True)
    
    def load_plugin_config(self, plugin_name: str) -> dict:
        """Load plugin-specific configuration."""
        config_file = self.config_dir / f"{plugin_name}.yaml"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        
        return {}
    
    def save_plugin_config(self, plugin_name: str, config: dict):
        """Save plugin-specific configuration."""
        config_file = self.config_dir / f"{plugin_name}.yaml"
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
```

### Global Configuration

```yaml
# ~/.strataregula/config.yaml
plugins:
  doe_runner:
    default_workers: 4
    cache_enabled: true
    log_level: "INFO"
  
  restaurant_config:
    default_format: "yaml"
    validation_strict: true

discovery:
  auto_load: true
  plugin_paths:
    - "~/.strataregula/plugins"
    - "/opt/strataregula/plugins"
```

## CLI Integration

### Plugin Commands

```python
import click

@click.group()
def plugin_cli():
    """Plugin management commands."""
    pass

@plugin_cli.command()
def list():
    """List all available plugins."""
    plugins = discover_plugins()
    
    click.echo("Available Plugins:")
    for name, plugin in plugins.items():
        info = plugin.get_info()
        click.echo(f"  {name}: {info['description']}")

@plugin_cli.command()
@click.argument('plugin_name')
@click.argument('command')
@click.option('--config', '-c', help='Configuration file')
def execute(plugin_name, command, config):
    """Execute plugin command."""
    plugins = discover_plugins()
    
    if plugin_name not in plugins:
        click.echo(f"Plugin '{plugin_name}' not found")
        return
    
    plugin = plugins[plugin_name]
    
    # Load configuration
    kwargs = {}
    if config:
        with open(config, 'r') as f:
            kwargs = yaml.safe_load(f)
    
    result = safe_plugin_execution(plugin, command, **kwargs)
    
    if result['status'] == 'success':
        click.echo("Command executed successfully")
    else:
        click.echo(f"Command failed: {result['message']}")
```

## Best Practices

### 1. Graceful Degradation

```python
def get_plugin_or_fallback(plugin_name: str, fallback=None):
    """Get plugin with fallback handling."""
    try:
        plugins = discover_plugins()
        return plugins.get(plugin_name, fallback)
    except Exception:
        return fallback
```

### 2. Plugin Health Checks

```python
def check_plugin_health(plugin):
    """Check if plugin is functioning correctly."""
    try:
        info = plugin.get_info()
        return {
            'healthy': True,
            'name': info.get('name', 'Unknown'),
            'version': info.get('version', 'Unknown')
        }
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e)
        }
```

### 3. Plugin Versioning

```python
from packaging import version

def check_plugin_compatibility(plugin, min_version: str):
    """Check if plugin meets minimum version requirement."""
    info = plugin.get_info()
    plugin_version = info.get('version', '0.0.0')
    
    return version.parse(plugin_version) >= version.parse(min_version)
```

### 4. Async Plugin Support

```python
import asyncio

async def async_plugin_execution(plugin, command, **kwargs):
    """Execute plugin command asynchronously if supported."""
    method = getattr(plugin, command, None)
    
    if not method:
        return {'status': 'error', 'message': 'Command not found'}
    
    if asyncio.iscoroutinefunction(method):
        return await method(**kwargs)
    else:
        # Run synchronous method in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, method, **kwargs)
```

## Plugin Ecosystem

### Available Plugins

- **DOE Runner** (`strataregula-doe-runner`): Batch experiment orchestrator
- **Restaurant Config** (`strataregula-restaurant-config`): Restaurant configuration management

### Plugin Development

See [Plugin Development Guide](plugin-development.md) for creating new plugins.

### Plugin Registry

Future versions may include a centralized plugin registry for easier discovery and installation.