# StrataRegula Code Style & Conventions

## Code Style Standards
- **Formatter**: ruff format (88 character line length)
- **Linter**: ruff check + mypy strict mode
- **Type Hints**: Required for all functions, classes, and variables
- **Python Version**: 3.11+ strict requirement
- **Import Style**: Combine imports, known-first-party = ["strataregula"]

## Naming Conventions
- **Classes**: PascalCase (EnhancedPatternExpander, ConfigCompiler)
- **Functions/Methods**: snake_case (expand_pattern_stream, compile_to_static_mapping)
- **Variables**: snake_case (expansion_rules, chunk_size)
- **Constants**: UPPER_SNAKE_CASE (SR_BENCH_MIN_RATIO)
- **Private Methods**: _leading_underscore (_expand_pattern_enhanced)
- **Files/Modules**: snake_case (pattern_expander.py, config_compiler.py)

## Documentation Standards
- **Docstrings**: Required for all public classes and methods
- **Type Annotations**: Comprehensive typing with generics where appropriate
- **Comments**: Explain complex algorithm logic, not obvious code
- **README**: Comprehensive with examples and architecture diagrams

## Code Organization Patterns
- **Separation of Concerns**: Core logic in core/, CLI in cli/, plugins in plugins/
- **Dependency Injection**: Plugin manager passed to core classes
- **Protocol-Based Design**: Use Protocol classes for interface definitions
- **Error Handling**: Specific exceptions with clear messages
- **Performance**: Caching strategies, streaming for large datasets

## Quality Gates
- **Test Coverage**: Minimum 80% (current: 87%)
- **Type Coverage**: 100% with mypy strict mode
- **Security**: bandit security scanning
- **Performance**: Golden metrics regression testing
- **Pre-commit**: Automated formatting, linting, and tests

## Architecture Patterns
- **Plugin System**: Hook-based extensibility with 5 integration points
- **Compilation Pipeline**: Multi-stage processing with caching
- **Streaming**: Support for large dataset processing
- **Configuration**: Hierarchical config with environment overrides
- **CLI Design**: Rich terminal output with multiple format options

## Example Code Structure
```python
from typing import Protocol, Dict, Any, Optional
from dataclasses import dataclass

class PatternExpander(Protocol):
    """Protocol for pattern expansion implementations."""
    
    def expand_pattern_stream(
        self, patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Expand patterns with streaming support."""
        ...

@dataclass
class EnhancedPatternExpander:
    """Enhanced pattern expander with plugin support."""
    
    chunk_size: int = 1000
    plugin_manager: Optional[PluginManager] = None
    
    def _expand_pattern_enhanced(
        self, pattern: str, value: Any
    ) -> Dict[str, Any]:
        """Internal pattern expansion with enhanced rules."""
        # Implementation details...
        return result
```

## Performance Considerations
- Use content-based caching for expensive operations
- Implement streaming for large datasets
- Profile critical paths with benchmarks
- Monitor memory usage with optional psutil integration
- Maintain golden metrics baselines for regression detection