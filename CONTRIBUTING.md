# Contributing to StrataRegula

Thank you for your interest in contributing to StrataRegula!

## Development Setup

### Prerequisites
- Python 3.8+
- Git

### Setup
```bash
git clone https://github.com/yourusername/strataregula.git
cd strataregula
pip install -e ".[dev,test,docs]"
pre-commit install
```

## Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation

3. **Test Changes**
   ```bash
   python tests/test_runner.py unit
   python tests/test_runner.py integration
   python tests/test_runner.py coverage
   ```

4. **Submit Pull Request**

## Code Style

- **Python**: Follow PEP 8
- **Type Hints**: Include for public APIs
- **Documentation**: Clear docstrings with examples
- **Testing**: Comprehensive test coverage

## Plugin Development

Use the 5 hook points: `pre_compilation`, `pattern_discovered`, `pre_expand`, `post_expand`, `compilation_complete`

```python
from strataregula.plugins.base import BasePlugin

class YourPlugin(BasePlugin):
    def pre_compilation(self, context):
        pass
```

## Quality Standards

- High test coverage
- Performance considerations
- Security best practices
- Clear documentation

## License

Contributions licensed under Apache License 2.0.
