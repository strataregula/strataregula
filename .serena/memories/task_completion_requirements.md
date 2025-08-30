# Task Completion Requirements for StrataRegula

## Commands to Run After Task Completion

### Quality Checks (Always Required)
```bash
# Code formatting and linting
make format
make lint

# Run all tests
make test
pytest -v

# Type checking
mypy strataregula/ --python-version 3.11
```

### Performance Validation
```bash
# Run benchmark guard for regression testing
python scripts/bench_guard.py

# Generate performance report
make golden-report

# Update performance baseline if needed
make golden-baseline
```

### Build and Package Verification
```bash
# Clean and rebuild
make clean
make build

# Verify package integrity
python -m build --check
```

### Pre-commit Validation
```bash
# Run pre-commit hooks
pre-commit run --all-files

# Install hooks if not already installed
pre-commit install
```

## Task Completion Checklist

### Before Marking Task Complete
- [ ] All code changes follow StrataRegula style conventions
- [ ] Type hints are provided for all functions and classes
- [ ] Tests pass without errors (`make test`)
- [ ] Code is properly formatted (`make format`) 
- [ ] Linting passes (`make lint`)
- [ ] Performance regression tests pass (`python scripts/bench_guard.py`)
- [ ] Documentation is updated if needed

### For Performance-Critical Changes
- [ ] Benchmark results meet minimum thresholds
- [ ] Golden metrics baseline updated if needed
- [ ] Performance impact documented

### For New Features
- [ ] Integration tests added
- [ ] Plugin compatibility verified
- [ ] CLI functionality tested
- [ ] Example usage documented

### For Bug Fixes
- [ ] Regression test added to prevent future occurrences
- [ ] Root cause documented
- [ ] Related components tested

## Environment-Specific Notes

### Windows Development
- Use `cmd /c` for environment variable setting: `cmd /c "set VAR=value && command"`
- Paths use backslashes: `scripts\bench_guard.py`
- PowerShell alternative: `$env:VAR="value"; command`

### CI/CD Integration
- GitHub Actions workflow validates all changes
- Automated performance regression detection
- Build artifacts saved for review
- Test results published as PR comments

## Common Commands Reference
```bash
# Quick quality check
make quick-check

# Full development setup
make dev-setup

# Release preparation
make release
```