# Strataregula

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**Strataregula** is a powerful YAML Configuration Pattern Compiler designed for hierarchical configuration management with wildcard pattern expansion.

## 🚀 Features

- **Pattern Expansion**: Wildcard pattern expansion (\*, \*\*) for large-scale configurations
- **Hierarchical Support**: 47 prefectures → 8 regions mapping for Japan
- **Multiple Formats**: Support for Python, JSON, and YAML output
- **Static Compilation**: O(1) lookup optimization with static mapping generation
- **Memory Efficient**: Streaming processing for large datasets
- **CLI Interface**: Simple `sr compile` command-line interface

## 🏗️ Architecture

```
strataregula/
├── core/           # Pattern expansion engine
├── cli/            # Command-line interface
├── hierarchy/      # Hierarchical region mapping
└── stream/         # Memory-efficient processing
```

## 📦 Installation

**Note: Not yet published to PyPI. Install from source:**

```bash
git clone https://github.com/strataregula/strataregula.git
cd strataregula
pip install -e .
```

For development:
```bash
pip install -e ".[dev,test]"
```

## 🎯 Quick Start

### Basic Usage

Compile a YAML configuration with pattern expansion:
```bash
strataregula compile input.yaml
```

Specify output format:
```bash
strataregula compile input.yaml --format python
strataregula compile input.yaml --format json
strataregula compile input.yaml --format yaml
```

Output to file:
```bash
strataregula compile input.yaml --output compiled.py
```

## 🔧 Advanced Usage

### Pattern Examples

Input YAML with wildcard patterns:
```yaml
services:
  web-*-*:
    port: 8080
    region: "*"
  api-**:
    port: 3000
```

Expands to specific configurations:
```python
# Generated Python output
services = {
    'web-tokyo-prod': {'port': 8080, 'region': 'tokyo'},
    'web-osaka-staging': {'port': 8080, 'region': 'osaka'},
    'api-user-service': {'port': 3000},
    # ... more expanded entries
}
```

## 🎨 CLI Commands

### `compile`
Compile YAML configuration with pattern expansion:
```bash
strataregula compile [OPTIONS] INPUT_FILE
```

Options:
- `--output, -o`: Output file (default: stdout)
- `--format, -f`: Output format (python, json, yaml)
- `--verbose, -v`: Enable verbose output
- `--help`: Show help message

## 🔌 Extensibility

Strataregula is designed for extensibility:

- **Pattern Expansion**: Customizable wildcard expansion rules
- **Output Formats**: Support for Python, JSON, and YAML outputs
- **Hierarchical Mapping**: Configurable region/prefecture mappings
- **Streaming Processing**: Memory-efficient handling of large datasets

## 🧪 Examples

### Example 1: Service Configuration

```yaml
# input.yaml
services:
  web-*:
    port: 8080
    region: "*"
  api-**-service:
    port: 3000
    database: "primary"
```

Compile to Python:
```bash
strataregula compile input.yaml --format python
```

Output:
```python
services = {
    'web-tokyo': {'port': 8080, 'region': 'tokyo'},
    'web-osaka': {'port': 8080, 'region': 'osaka'},
    'api-user-service': {'port': 3000, 'database': 'primary'},
    'api-auth-service': {'port': 3000, 'database': 'primary'},
}
```

### Example 2: Regional Configuration

```yaml
# regional.yaml
regions:
  "*":
    timezone: "Asia/Tokyo"
    language: "ja"
```

Expands to all 47 prefectures with hierarchical grouping into 8 regions.

## 🚀 Performance

- **Static Compilation**: O(1) lookup with pre-compiled mappings
- **Memory Efficient**: Streaming processing for large configurations
- **Fast Pattern Matching**: Optimized wildcard expansion algorithms
- **Scalable**: Handles thousands of pattern expansions efficiently

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/strataregula/strataregula.git
cd strataregula
pip install -e ".[dev]"
pytest
```

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with modern Python async/await patterns
- Inspired by Unix pipeline philosophy
- Designed for cloud-native configuration management
- Community-driven development approach

## 📞 Support

- **Documentation**: [https://strataregula.readthedocs.io/](https://strataregula.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/strataregula/strataregula/issues)
- **Discussions**: [GitHub Discussions](https://github.com/strataregula/strataregula/discussions)
- **Email**: support@strataregula.dev

---

**Strataregula** - Hierarchical Configuration Management with Pattern Expansion.
## 📊 Performance Benchmarks

### 🚀 Service Lookup Performance

![Performance Comparison](docs/images/benchmark_performance.png)

**Results:**
- **Direct Map**: 500,000 ops/sec (50x faster than fnmatch)
- **Compiled Tree**: 50,000 ops/sec (5x faster than fnmatch) 
- **fnmatch baseline**: 10,000 ops/sec

# Performance optimized for large-scale pattern processing

### ⚡ Compilation Performance

![Compilation Performance](docs/images/benchmark_compilation.png)

**Compilation Speed:**
- Small config: 2ms (10 entries)
- Medium config: 45ms (100 entries)
- Large config: 180ms (500 entries)

### 💾 Memory Usage

![Memory Usage](docs/images/benchmark_memory.png)

**Memory Efficiency:**
- Total system memory: 119MB
- Pattern Expander: 44MB (most intensive component)
- Core system: 12MB (lightweight base)

### 📋 Performance Dashboard

![Performance Dashboard](docs/images/benchmark_dashboard.png)

**All performance targets achieved:**
- ✅ Pattern Expansion: >10,000 patterns/sec
- ✅ Compilation: <100ms for medium configs  
- ✅ Memory Usage: <200MB total
- ✅ Service Lookup: >100,000 ops/sec

[View Interactive Analysis (develop branch)](https://github.com/strataregula/strataregula/tree/develop/notebooks/benchmark_results.ipynb) | [Run Benchmarks (develop branch)](https://github.com/strataregula/strataregula/tree/develop/scripts/run_benchmarks.py)
