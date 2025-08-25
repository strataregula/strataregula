# Strataregula Documentation

Welcome to the comprehensive documentation for Strataregula and its ecosystem.

## Overview

**Strataregula** is a powerful YAML Configuration Pattern Compiler with PiPE (Pattern Input Processing Engine) command chaining, designed for modern configuration management and automation workflows.

### Key Features

- **🔄 Pattern Expansion**: Wildcard pattern expansion with hierarchical Japanese geography support
- **⚡ High Performance**: O(1) lookup with compiled static modules and LRU caching
- **🔧 Plugin Ecosystem**: Rich plugin system with independent architecture
- **📊 Batch Processing**: Execute predefined experiment cases with standardized metrics
- **🎯 CLI Integration**: Rich command-line interface with streaming support
- **🏗️ Modern Architecture**: Type-safe dataclass-based configuration and async support

## Quick Start

### Installation

```bash
pip install strataregula
```

### Basic Usage

```bash
# Compile configuration patterns
sr compile config.yaml --output expanded.py --format python

# Plan mode for analysis
sr compile config.yaml --plan

# Get statistics
sr compile config.yaml --stats
```

### Plugin Usage

```bash
# Install DOE Runner plugin
pip install strataregula-doe-runner

# Execute batch experiments
srd run --cases cases.csv --out metrics.csv --max-workers 4
```

## Documentation Structure

### 📚 Core Documentation

#### [Getting Started Examples](examples/getting-started.md)
Practical examples to get you started with Strataregula, from basic pattern expansion to advanced pipeline creation.

#### [API Reference](api/index.md)
Comprehensive API documentation for Strataregula core and plugins, including data models and error handling.

### 🔌 Plugin System

#### [Plugin Development Guide](plugins/plugin-development.md)
Learn how to create plugins for the Strataregula ecosystem with independent architecture and best practices.

#### [Plugin Integration Guide](plugins/plugin-integration.md)
How to integrate plugins with Strataregula, including discovery, configuration, and CLI integration.

#### [DOE Runner Plugin](plugins/doe-runner.md)
Complete documentation for the batch experiment orchestrator plugin, including usage examples and configuration.

### 🎓 Tutorials

#### [Plugin Development Tutorial](tutorials/plugin-development-tutorial.md)
Step-by-step tutorial for building your own Strataregula plugin, including project structure, testing, and distribution.

## Architecture

```
strataregula/
├── core/              # Core compilation engine
│   ├── compiler.py    # Configuration compiler
│   ├── pattern_expander.py  # Pattern expansion engine
│   └── config.py      # Configuration models
├── cli/               # Command-line interface
│   ├── main.py        # Main CLI entry point
│   └── commands/      # CLI command implementations
├── pipe/              # PiPE command chaining
├── hooks/             # Event-driven hooks
├── di/                # Dependency injection
└── plugins/           # Plugin discovery system
```

## Plugin Ecosystem

### Available Plugins

| Plugin | Description | Status |
|--------|-------------|--------|
| **DOE Runner** | Batch experiment orchestrator (cases.csv → metrics.csv) | ✅ Stable |
| **Restaurant Config** | Restaurant configuration management | 🚧 Development |
| **Log Analyzer** | Log analysis and metrics extraction | 📖 Tutorial |

### Plugin Architecture

- **🔄 Independent Design**: Plugins work standalone without Strataregula
- **🔍 Automatic Discovery**: Python entry points for plugin discovery
- **🧩 Modular Components**: Clear separation with well-defined interfaces
- **🔧 Extensible Adapters**: Pluggable execution backends

## Core Features

### Pattern Expansion Engine

Transform wildcard patterns into specific configurations:

```yaml
# Input patterns
services:
  - "edge.*.gateway"    # Expands to 47 prefectures
  - "api.*.service"     # Hierarchical expansion
```

```python
# Generated output (179 expanded services)
SERVICES = [
    "edge.tokyo.gateway",
    "edge.osaka.gateway", 
    "edge.hokkaido.gateway",
    # ... all 47 prefectures
]
```

### Performance Metrics

- **Expansion Results**: 13 input patterns → 179 expanded services
- **Processing Time**: <10ms compilation time
- **Memory Usage**: ~44MB peak memory usage  
- **Hierarchy Support**: 47 prefectures → 8 regions mapping

### Static Module Generation

Generate optimized Python modules with O(1) lookup:

```python
# Generated lookup functions
def lookup_service(pattern: str) -> List[str]:
    """O(1) service lookup by pattern."""
    return SERVICE_MAP.get(pattern, [])

def lookup_by_region(region: str) -> List[str]:
    """Lookup services by region."""
    return REGION_MAP.get(region, [])
```

## CLI Commands

### Core Commands

- **`sr compile`** - Compile configuration patterns with various output formats
- **`sr process`** - Process data through command pipelines
- **`sr create`** - Create reusable pipelines
- **`sr run`** - Execute saved pipelines  
- **`sr list`** - List available commands and pipelines

### Plugin Commands

- **`srd run`** - DOE Runner: Execute batch experiments
- **`srd validate`** - Validate case definitions
- **`sla analyze`** - Log Analyzer: Analyze log files

## Configuration Examples

### Basic Configuration

```yaml
# config.yaml
services:
  web:
    - "api.*.service"
    - "web.*.frontend"
  infrastructure:
    - "edge.*.gateway"
    - "cache.*.redis"

regions:
  kanto: ["tokyo", "chiba", "saitama", "kanagawa"]
  kansai: ["osaka", "kyoto", "hyogo", "nara"]
```

### DOE Runner Cases

```csv
case_id,backend,cmd_template,timeout_s,threshold_p95
test-01,shell,"echo 'p95=0.05 throughput_rps=1000'",10,0.06
test-02,dummy,"simulation test",10,0.10
test-03,simroute,"python -m simroute_cli --seed {seed}",120,0.12
```

## Best Practices

### Configuration Management

1. **Use Hierarchical Patterns**: Leverage region hierarchy for scalable configurations
2. **Enable Caching**: Use LRU caching for repeated pattern expansions
3. **Memory Limits**: Set appropriate memory limits for large datasets
4. **Static Generation**: Compile to static modules for production use

### Plugin Development

1. **Independent Architecture**: Avoid hard dependencies on Strataregula
2. **Entry Point Discovery**: Use Python entry points for automatic discovery
3. **Consistent Interfaces**: Follow standard plugin patterns
4. **Comprehensive Testing**: Include unit, integration, and performance tests

### Performance Optimization

1. **Streaming Processing**: Use streaming for large datasets
2. **Parallel Execution**: Leverage multi-worker execution for batch processing
3. **Cache Management**: Configure cache sizes based on workload
4. **Memory Monitoring**: Monitor memory usage with built-in limits

## Development

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Follow coding standards (ruff, mypy)
5. Submit a pull request

### Testing

```bash
# Run core tests
pytest tests/ -v --cov=strataregula

# Run plugin tests
pytest tests/plugins/ -v

# Performance tests
pytest tests/ -m performance
```

### Development Setup

```bash
git clone https://github.com/strataregula/strataregula.git
cd strataregula
pip install -e ".[dev]"
pre-commit install
```

## Troubleshooting

### Common Issues

1. **Pattern Not Expanding**: Check wildcard syntax and hierarchy file
2. **Plugin Not Found**: Verify entry point registration in pyproject.toml
3. **Memory Issues**: Adjust memory_limit_mb parameter
4. **Performance**: Enable caching and use appropriate cache sizes

### Debug Mode

```bash
# Enable verbose logging
sr compile config.yaml --verbose --debug

# Check plugin discovery
python -c "import pkg_resources; print(list(pkg_resources.iter_entry_points('strataregula.plugins')))"
```

## Version History

### v0.1.1 (Current)
- ✅ Comprehensive test suite (90%+ coverage)
- ✅ Enhanced pattern expansion with hierarchy support
- ✅ DOE Runner plugin with batch orchestration
- ✅ Performance optimizations and memory management
- ✅ Bug fixes and stability improvements

### v0.1.0
- 🎯 Enhanced Pattern Expansion Engine with 47 prefectures support
- ⚡ CLI Integration with multiple output formats
- 🏗️ Static Module Generation with O(1) lookup
- 📊 Performance: 179 services, <10ms compilation, ~44MB memory

## Support

- **Documentation**: This site
- **Repository**: [GitHub](https://github.com/strataregula/strataregula)
- **Issues**: [GitHub Issues](https://github.com/strataregula/strataregula/issues)
- **Email**: support@strataregula.dev

---

**Strataregula** - Where configuration meets automation, powered by pattern expansion and plugin ecosystem.