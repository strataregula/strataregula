# API Reference

This section provides comprehensive API documentation for Strataregula and its ecosystem.

## Core API

### Configuration Compiler

The main configuration compiler for pattern expansion and template generation.

```python
from strataregula.core.compiler import ConfigCompiler
from strataregula.core.config import CompilationConfig

# Initialize compiler
config = CompilationConfig(
    input_path="config.yaml",
    output_path="output.py",
    output_format="python",
    enable_statistics=True
)

compiler = ConfigCompiler(config)
result = compiler.compile()
```

#### ConfigCompiler

- **`__init__(self, config: CompilationConfig)`** - Initialize compiler with configuration
- **`compile(self) -> CompilationResult`** - Execute compilation process
- **`validate_input(self) -> bool`** - Validate input configuration
- **`get_statistics(self) -> CompilationStats`** - Get compilation statistics

### Pattern Expansion

Enhanced pattern expansion with wildcard and hierarchy support.

```python
from strataregula.core.pattern_expander import EnhancedPatternExpander
from strataregula.core.region_hierarchy import RegionHierarchy

# Initialize expander
hierarchy = RegionHierarchy.from_yaml("prefectures.yaml")
expander = EnhancedPatternExpander(hierarchy=hierarchy)

# Expand patterns
expanded = expander.expand_pattern("edge.*.gateway")
```

#### EnhancedPatternExpander

- **`expand_pattern(self, pattern: str) -> List[str]`** - Expand single pattern
- **`expand_patterns(self, patterns: List[str]) -> Dict[str, List[str]]`** - Expand multiple patterns
- **`compile_to_static_mapping(self, patterns: List[str]) -> Dict[str, Any]`** - Compile to static mapping

### CLI Interface

Command-line interface for Strataregula operations.

```python
from strataregula.cli.main import main
from strataregula.cli.commands.compile import CompileCommand

# Access CLI programmatically
compile_cmd = CompileCommand()
result = compile_cmd.execute(
    input_file="config.yaml",
    output_file="output.py",
    format="python"
)
```

#### CLI Commands

- **`sr compile`** - Compile configuration patterns
- **`sr process`** - Process data through command pipelines
- **`sr create`** - Create new pipelines
- **`sr run`** - Execute saved pipelines
- **`sr list`** - List available commands and pipelines

## Plugin API

### Plugin Base Interface

All plugins follow this interface pattern:

```python
class PluginInterface:
    name: str
    version: str
    description: str
    author: str
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin metadata."""
        pass
    
    def validate_input(self, **kwargs) -> bool:
        """Validate plugin input."""
        pass
```

### DOE Runner Plugin

Batch experiment orchestrator plugin.

```python
from strataregula_doe_runner.plugin import DOERunnerPlugin

plugin = DOERunnerPlugin()

# Execute cases
result = plugin.execute_cases(
    cases_path="cases.csv",
    metrics_path="metrics.csv",
    max_workers=4,
    force=False,
    verbose=True
)
```

#### DOERunnerPlugin Methods

- **`execute_cases(self, **kwargs) -> Dict[str, Any]`** - Execute cases from CSV
- **`validate_cases(self, cases_path: str) -> Dict[str, Any]`** - Validate case format
- **`get_cache_status(self, cases_path: str) -> Dict[str, Any]`** - Check cache status
- **`clear_cache(self, cases_path: str) -> Dict[str, Any]`** - Clear execution cache
- **`get_adapters(self) -> Dict[str, Any]`** - List available adapters

#### Execution Parameters

```python
# execute_cases parameters
{
    'cases_path': str,           # Path to cases.csv
    'metrics_path': str,         # Output metrics.csv path
    'max_workers': int,          # Parallel execution workers (default: 1)
    'force': bool,               # Force re-execution (ignore cache)
    'dry_run': bool,             # Validate without execution
    'verbose': bool,             # Enable verbose output
    'timeout': int,              # Global timeout override
    'backend_filter': str        # Filter by backend type
}
```

#### Return Format

```python
{
    'status': str,               # 'success' | 'error'
    'exit_code': int,            # 0 (success) | 2 (threshold) | 3 (error)
    'message': str,              # Status message
    'stats': {
        'total_cases': int,
        'successful': int,
        'failed': int,
        'timeout': int,
        'cached': int,
        'execution_time': float,
        'threshold_violations': List[str]
    }
}
```

## Data Models

### Configuration Models

```python
from strataregula.core.config import CompilationConfig
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class CompilationConfig:
    input_path: str
    output_path: str
    output_format: str = "python"
    hierarchy_path: Optional[str] = None
    enable_caching: bool = True
    cache_size: int = 128
    enable_statistics: bool = False
    memory_limit_mb: int = 200
    patterns_filter: Optional[List[str]] = None
```

### DOE Runner Models

```python
from strataregula_doe_runner.core.models import CaseDefinition, ExecutionResult
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class CaseDefinition:
    case_id: str
    backend: str
    cmd_template: str
    timeout_s: int
    seed: Optional[int] = None
    retries: int = 0
    resource_group: str = "default"
    expected_p95: Optional[float] = None
    expected_p99: Optional[float] = None
    threshold_p95: Optional[float] = None
    threshold_p99: Optional[float] = None

@dataclass
class ExecutionResult:
    case_id: str
    status: str  # OK | FAIL | TIMEOUT
    run_seconds: float
    p95: Optional[float]
    p99: Optional[float]
    throughput_rps: float
    errors: int = 0
    ts_start: Optional[datetime] = None
    ts_end: Optional[datetime] = None
```

## Error Handling

### Exception Types

```python
from strataregula.exceptions import (
    StratareglaException,
    ConfigurationError,
    PatternExpansionError,
    CompilationError,
    PluginError
)

try:
    compiler.compile()
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except PatternExpansionError as e:
    print(f"Pattern expansion failed: {e}")
except CompilationError as e:
    print(f"Compilation failed: {e}")
```

### Error Response Format

```python
{
    'status': 'error',
    'error_code': str,           # Error classification
    'message': str,              # Human-readable message
    'details': Dict[str, Any],   # Additional error context
    'timestamp': str,            # ISO timestamp
    'traceback': Optional[str]   # Stack trace (debug mode)
}
```

## Utilities

### Pattern Utilities

```python
from strataregula.utils.patterns import (
    is_pattern,
    extract_wildcards,
    validate_pattern_syntax
)

# Check if string contains patterns
if is_pattern("edge.*.gateway"):
    wildcards = extract_wildcards("edge.*.gateway")
    # Returns: ['*']
```

### File Utilities

```python
from strataregula.utils.files import (
    safe_write_file,
    load_yaml_safe,
    ensure_directory
)

# Safe file operations
data = load_yaml_safe("config.yaml")
ensure_directory("output/")
safe_write_file("output/result.py", content)
```

### Logging

```python
from strataregula.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Processing started")
logger.error("Processing failed", exc_info=True)
```

## Performance Considerations

### Memory Management

- Use streaming processors for large datasets
- Configure appropriate cache sizes
- Monitor memory usage with memory_limit_mb parameter

### Concurrent Execution

- DOE Runner supports parallel execution with max_workers
- Thread-safe caching with LRU eviction
- Resource grouping for execution control

### Caching

- Pattern expansion results are cached
- Case execution results cached by case_hash
- Configurable cache sizes and TTL

## Version Compatibility

| Component | Python | Dependencies |
|-----------|--------|--------------|
| Strataregula Core | 3.11+ | click, rich, pyyaml, psutil |
| DOE Runner Plugin | 3.11+ | pydantic, pandas (optional) |
| Plugin System | 3.11+ | pkg_resources, setuptools |

## Migration Guide

### From v0.1.0 to v0.1.1

- Enhanced test coverage and performance improvements
- No breaking API changes
- Deprecated datetime handling warnings fixed

### Plugin Migration

- Plugins using old architecture should migrate to independent pattern
- Remove hard Strataregula dependencies
- Use entry points for discovery