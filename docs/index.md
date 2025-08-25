# Strataregula Documentation

**Strataregula** is a YAML Configuration Pattern Compiler designed for hierarchical configuration management with wildcard pattern expansion.

## What It Does

Strataregula takes YAML configurations with wildcard patterns and expands them into concrete service configurations, with built-in support for Japanese prefecture-to-region hierarchical mapping.

## Core Features ✅

- **Pattern Expansion**: Wildcard patterns (`*`, `**`) expand to specific configurations
- **Hierarchical Support**: 47 Japanese prefectures mapped to 8 regions  
- **Multiple Output Formats**: Python, JSON, and YAML generation
- **CLI Interface**: Simple `strataregula compile` command
- **Memory Efficient**: Streaming processing for large datasets

## Installation

**Note: Not yet published to PyPI. Install from source:**

```bash
git clone https://github.com/strataregula/strataregula.git
cd strataregula
pip install -e .
```

## Quick Example

**Input** (`services.yaml`):
```yaml
services:
  api-*:
    port: 8080
    region: "*"
  cache-**:
    port: 6379
```

**Command**:
```bash
strataregula compile services.yaml --format python
```

**Output**:
```python
services = {
    'api-tokyo': {'port': 8080, 'region': 'tokyo'},
    'api-osaka': {'port': 8080, 'region': 'osaka'},
    # ... all 47 prefectures
    'cache-redis': {'port': 6379},
    'cache-memcached': {'port': 6379},
    # ... expanded patterns
}
```

## Documentation

- **[Installation Guide](getting-started/installation.md)** - Setup and installation
- **[Examples](../examples/)** - Practical usage examples
- **CLI Reference** - `strataregula compile --help`

## Architecture

```
strataregula/
├── core/           # Pattern expansion engine
├── cli/            # Command-line interface  
├── hierarchy/      # Prefecture/region mapping
├── stream/         # Memory-efficient processing
└── json_processor/ # JSON processing utilities
```

## Examples Directory

- **[hierarchy_test.py](../examples/hierarchy_test.py)** - Test hierarchical mapping
- **[sample_prefectures.yaml](../examples/sample_prefectures.yaml)** - Prefecture examples
- **[sample_traffic.yaml](../examples/sample_traffic.yaml)** - Traffic routing example

## CLI Usage

```bash
# Basic compilation
strataregula compile config.yaml

# Specify output format
strataregula compile config.yaml --format json

# Save to file  
strataregula compile config.yaml --output result.py

# Verbose output
strataregula compile config.yaml --verbose
```

## Support

- **Repository**: [GitHub](https://github.com/strataregula/strataregula)
- **Issues**: [Report Problems](https://github.com/strataregula/strataregula/issues)  
- **Email**: team@strataregula.com

---

**Strataregula v0.1.1** - Production-ready pattern expansion for configuration management.