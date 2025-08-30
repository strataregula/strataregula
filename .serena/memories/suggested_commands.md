# Suggested Commands for StrataRegula Development

## Development Commands

### Setup & Installation
```bash
# Install development environment
make install

# Install with performance monitoring
pip install 'strataregula[performance]'
```

### Testing
```bash
# Run all tests
make test
pytest -v

# Run specific test categories
pytest -m unit
pytest -m integration  
pytest -m performance
```

### Code Quality
```bash
# Run linting (ruff + mypy)
make lint

# Format code
make format
ruff format .

# Individual checks
ruff check .
mypy strataregula/ --python-version 3.11
```

### Performance & Regression Testing
```bash
# Capture performance baseline
make golden-baseline

# Check for performance regressions  
make golden-check

# Generate performance report (non-failing)
make golden-report

# Clean performance reports
make golden-clean
```

### Build & Release
```bash
# Clean build artifacts
make clean

# Build distribution
make build

# Full release workflow
make release
```

## Core CLI Commands

### Basic Usage
```bash
# Compile YAML with pattern expansion
strataregula compile --traffic config.yaml

# With custom output format
strataregula compile --traffic config.yaml --format json

# With prefecture hierarchy
strataregula compile --traffic services.yaml --prefectures regions.yaml
```

### Advanced Features
```bash
# Visualize compiled configuration
strataregula compile --traffic config.yaml --dump-compiled-config --dump-format tree

# Environment diagnostics
strataregula doctor
strataregula doctor --fix-suggestions

# Show usage examples
strataregula examples
```

## Performance Testing
```bash
# Run benchmark guard script
python scripts/bench_guard.py

# With custom thresholds
SR_BENCH_MIN_RATIO=50 SR_BENCH_MAX_P95_US=50 python scripts/bench_guard.py
```

## Utility Commands (Windows)
```bash
# Directory operations
dir /s          # List files recursively
cd /d C:\path   # Change directory with drive

# Search operations  
findstr /s "pattern" *.py   # Search in files
where python                # Find executable location

# Process management
tasklist | findstr python   # Find Python processes
taskkill /f /im python.exe  # Kill Python processes

# Git operations
git status
git branch
git log --oneline -10
```

## Environment Variables
```bash
# Performance test configuration
set SR_BENCH_MIN_RATIO=50
set SR_BENCH_MAX_P95_US=50
set SR_BENCH_WARMUP=1000
set SR_BENCH_N=100000

# Plugin configuration
set STRATAREGULA_PLUGINS_ENABLED=true
set STRATAREGULA_VERBOSE=true
```