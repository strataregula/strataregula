# Strataregula

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**Strataregula** is a YAML Configuration Pattern Compiler for hierarchical configuration management with wildcard pattern expansion.

## Features

- **🔍 Pattern Expansion**: Wildcard patterns (`*`, `**`) expand to specific configurations
- **🗾 Hierarchical Mapping**: Built-in support for 47 Japanese prefectures → 8 regions
- **📄 Multiple Formats**: Generate Python, JSON, or YAML output
- **⚡ Memory Efficient**: Streaming processing for large configurations
- **🖥️ Simple CLI**: Single `strataregula compile` command

## Quick Example

**Input** (`config.yaml`):
```yaml
services:
  api-*:
    port: 8080
    region: "*"
```

**Command**:
```bash
strataregula compile config.yaml --format python
```

**Output**:
```python
services = {
    'api-tokyo': {'port': 8080, 'region': 'tokyo'},
    'api-osaka': {'port': 8080, 'region': 'osaka'},
    'api-kyoto': {'port': 8080, 'region': 'kyoto'},
    # ... expands to all 47 prefectures
}
```

## Installation

**Install from source** (not yet on PyPI):

```bash
git clone https://github.com/strataregula/strataregula.git
cd strataregula
pip install -e .
```

## Usage

### Basic Compilation
```bash
# Compile and print to stdout
strataregula compile config.yaml

# Generate Python format
strataregula compile config.yaml --format python

# Save to file
strataregula compile config.yaml --output result.py

# JSON format
strataregula compile config.yaml --format json --output config.json

# YAML format  
strataregula compile config.yaml --format yaml --output expanded.yaml

# Verbose output
strataregula compile config.yaml --verbose
```

### Pattern Examples

**Single wildcard** (`*`): Matches one segment
```yaml
web-*:  # → web-tokyo, web-osaka, etc.
```

**Double wildcard** (`**`): Matches any segments  
```yaml
cache-**:  # → cache-redis, cache-memcached, etc.
```

**Region expansion**:
```yaml
"*":
  timezone: "Asia/Tokyo"
# Expands to all 47 prefectures with timezone setting
```

## Examples

See the [`examples/`](examples/) directory:
- **[sample_prefectures.yaml](examples/sample_prefectures.yaml)** - Prefecture hierarchy example
- **[sample_traffic.yaml](examples/sample_traffic.yaml)** - Traffic routing patterns
- **[hierarchy_test.py](examples/hierarchy_test.py)** - Test script for hierarchy mapping

## Architecture

```
strataregula/
├── core/           # Pattern expansion engine
├── cli/            # Command-line interface
├── hierarchy/      # Prefecture/region mapping
├── stream/         # Memory-efficient processing
└── json_processor/ # JSON processing utilities
```

## Performance

- **Pattern Processing**: Handles thousands of patterns efficiently
- **Memory Usage**: Streaming processing keeps memory usage low
- **Output Generation**: Fast static compilation with O(1) lookups

## Contributing

```bash
git clone https://github.com/strataregula/strataregula.git
cd strataregula
pip install -e ".[dev,test]"
pytest
```

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/strataregula/strataregula/issues)
- **Discussions**: [GitHub Discussions](https://github.com/strataregula/strataregula/discussions)  
- **Email**: team@strataregula.com

---

**Strataregula v0.1.1** - Simple, powerful configuration pattern expansion.