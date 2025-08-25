# Plugin Development Guide

This guide covers how to develop plugins for the Strataregula ecosystem, using the DOE Runner plugin as a reference implementation.

## Plugin Architecture Philosophy

Strataregula uses an **independent plugin architecture** that emphasizes loose coupling and standalone functionality.

### Core Principles

1. **Independence**: Plugins should work standalone without Strataregula
2. **Discoverability**: Use Python entry points for automatic plugin discovery
3. **Modularity**: Clear separation of concerns with well-defined interfaces
4. **Extensibility**: Pluggable components for different execution backends

## Plugin Structure

### Basic Plugin Class

```python
class MyPlugin:
    """Independent plugin for Strataregula."""
    
    # Plugin metadata
    name = "my-plugin"
    version = "0.1.0"
    description = "Description of plugin functionality"
    author = "Plugin Author"
    
    def __init__(self):
        """Initialize plugin."""
        self._initialize_components()
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "supported_commands": [
                "command1",
                "command2",
            ]
        }
    
    def command1(self, **kwargs) -> Dict[str, Any]:
        """Execute command1."""
        try:
            # Implementation here
            return {
                "status": "success",
                "result": "command1 executed"
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": str(e)
            }

# Plugin factory function
def create_plugin():
    """Factory function to create plugin instance."""
    return MyPlugin()
```

### Entry Point Registration

In `pyproject.toml`:

```toml
[project.entry-points."strataregula.plugins"]
"my-plugin" = "my_package.plugin:MyPlugin"
```

## Reference Implementation

The [DOE Runner plugin](./doe-runner.md) serves as a complete reference implementation demonstrating all these patterns.

## Best Practices

### 1. Independent Functionality
- Work standalone without Strataregula
- Use entry points for discovery
- Avoid tight coupling

### 2. Error Handling
- Return consistent response formats
- Provide meaningful error messages
- Handle edge cases gracefully

### 3. Configuration Management
- Make plugins configurable
- Provide sensible defaults
- Support runtime configuration

## Common Pitfalls

1. **Hard Dependencies**: Avoid requiring Strataregula for basic functionality
2. **Circular Imports**: Use typing forward references and lazy imports
3. **Error Silencing**: Always return meaningful error messages
4. **Configuration Hardcoding**: Make plugins configurable
5. **Poor Documentation**: Provide clear usage examples