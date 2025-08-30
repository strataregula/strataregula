# Contributing

- PR は小さく、1 PR = 1 目的。
- `docs/run/*.md` に記録する Runログの Summary は必ず非空にしてください。
- CI must be green before merging.

## Development Setup

### Prerequisites
- Python 3.11+ (pinned requirement)
- Git
- Optional: pre-commit for code quality

### Setup
```bash
git clone https://github.com/strataregula/strataregula.git
cd strataregula
pip install -e ".[dev,test,performance]"
pre-commit install
```

## Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow existing code style (ruff + mypy enforced)
   - Add tests for new functionality
   - Update documentation
   - Consider performance impact

3. **Test Changes**
   ```bash
   # Unit tests
   pytest tests/ -m "not integration"
   
   # Integration tests  
   pytest tests/ -m integration
   
   # Coverage report
   pytest --cov=strataregula --cov-report=html
   
   # Performance benchmarks
   python scripts/bench_guard.py
   ```

4. **Quality Checks**
   ```bash
   # Code formatting and linting
   ruff format .
   ruff check .
   
   # Type checking
   mypy strataregula/
   
   # Security scanning
   bandit -r strataregula/
   ```

5. **Submit Pull Request**

## Code Style

- **Python**: Ruff (modern replacement for Black + flake8)
- **Type Hints**: Strict mypy enforcement for all modules
- **Documentation**: Clear docstrings with examples and type information
- **Testing**: ≥80% coverage required
- **Performance**: Benchmarks must pass (see Performance Guidelines below)

## Plugin Development

StrataRegula's plugin architecture supports 5 hook points:
- `pre_compilation`: Before compilation starts
- `pattern_discovered`: When new patterns are found
- `pre_expand`: Before pattern expansion
- `post_expand`: After pattern expansion  
- `compilation_complete`: After compilation finishes

```python
from strataregula.plugins.base import BasePlugin

class YourPlugin(BasePlugin):
    def pre_compilation(self, context):
        """Called before compilation begins"""
        pass
    
    def pattern_discovered(self, pattern, context):
        """Called when a new pattern is discovered"""
        pass
```

## Performance Guidelines

StrataRegula includes automated performance regression testing:

### Benchmark Requirements
- All PRs must pass `python scripts/bench_guard.py`
- Performance must not regress beyond acceptable thresholds
- Critical paths (config compilation, pattern expansion) are strictly monitored

### Running Benchmarks
```bash
# Full benchmark suite
python scripts/bench_guard.py

# Quick check (reduced iterations)
SR_BENCH_N=10000 python scripts/bench_guard.py

# Debug benchmark results
cat bench_guard.json | python -m json.tool
```

### Performance Optimization
- Focus on hot paths in `strataregula.core.compiler` and `strataregula.core.pattern_expander`
- Use profiling tools: `cProfile`, `memory_profiler`
- Consider algorithmic improvements: O(n²) → O(n log n)
- Minimize memory allocations in tight loops

## Quality Standards

### Automated Quality Gates
- **Tests**: pytest with ≥80% coverage
- **Types**: mypy strict mode
- **Style**: ruff formatting and linting
- **Security**: bandit scanning
- **Performance**: benchmark regression testing

### Development Practices
- Write tests before implementation (TDD)
- Performance-conscious coding
- Security-first development
- Clear, self-documenting code
- Comprehensive docstrings

## Advanced Development

### Core Architecture
- **strataregula.core**: Compilation engine and pattern processing
- **strataregula.plugins**: Extensible plugin system
- **strataregula.cli**: Command-line interface
- **strataregula.hierarchy**: Configuration layering
- **strataregula.golden**: Performance regression testing

### Plugin System
StrataRegula's plugin manager supports:
- Dynamic plugin discovery
- Dependency injection
- Error handling and recovery
- Performance monitoring

### Performance Critical Paths
1. **Pattern Compilation**: `config_compiler.py`
2. **Pattern Expansion**: `pattern_expander.py`  
3. **Config Interning**: `passes/intern.py`
4. **Kernel Operations**: `kernel.py`

## Documentation

All contributions should include:
- **Code Documentation**: Comprehensive docstrings
- **API Documentation**: For public interfaces
- **Examples**: Working code samples
- **Performance Notes**: For performance-sensitive changes

Link to detailed developer documentation: [docs/README_FOR_DEVELOPERS.md](docs/README_FOR_DEVELOPERS.md)

## License

By contributing, you agree that your contributions will be licensed under Apache License 2.0.
