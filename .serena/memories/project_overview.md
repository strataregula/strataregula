# StrataRegula Project Overview

## Purpose
StrataRegula is a YAML Configuration Pattern Compiler for hierarchical configuration management with wildcard pattern expansion, designed for enterprise-scale configuration processing. It compiles configuration patterns into optimized static mappings for high-performance lookups.

## Tech Stack
- **Language**: Python 3.11+ (strict requirement)
- **Core Dependencies**: 
  - click>=7.0.0 (CLI interface)
  - rich>=10.0.0 (terminal output formatting)
  - pyyaml>=5.4.0 (YAML processing)
  - typing-extensions>=3.10.0
- **Development Tools**: 
  - pytest (testing), mypy (type checking), ruff (linting/formatting)
  - pre-commit hooks, bandit (security), build/twine (packaging)
- **Optional**: psutil (performance monitoring), matplotlib/seaborn (visualizations)

## Architecture Overview
```
strataregula/
├── core/                    # Core pattern expansion engine
│   ├── compiler.py         # High-performance pattern compiler  
│   ├── config_compiler.py  # Main compilation with plugin integration
│   ├── pattern_expander.py # Enhanced pattern expansion (EnhancedPatternExpander class)
│   └── compatibility.py    # Environment compatibility checking
├── plugins/                 # Plugin system (v0.2.0)
│   ├── manager.py          # Plugin lifecycle management
│   └── samples/            # Sample plugin implementations  
├── cli/                    # Command-line interface
│   ├── main.py            # Main CLI with diagnostics
│   └── compile_command.py  # Compilation with visualization
└── data/                   # Data sources and hierarchy definitions
```

## Key Features
- **Pattern Expansion**: 100K+ patterns/sec with wildcard support (service.*.response → service.web.response, service.api.response)
- **Plugin System**: 5 hook points for extending functionality
- **Performance Monitoring**: Built-in regression detection system
- **Multiple Output Formats**: JSON, YAML, Python, Table, Tree visualization
- **Hierarchical Processing**: Prefecture/region-based data organization
- **Enterprise Features**: Caching, streaming, diagnostics

## Performance Characteristics
- Pattern expansion: ~100,000-400,000 patterns/second
- Plugin overhead: <5% when enabled
- Memory efficient with streaming support
- Fast compilation for typical configs (1-10MB)

## Current Status
- **v0.2.0**: Production ready with complete plugin system
- 87% test coverage, enterprise-grade quality
- 1,758 lines of plugin architecture, 28 classes
- Fully backward compatible with v0.1.x