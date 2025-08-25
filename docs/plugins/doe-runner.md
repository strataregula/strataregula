# DOE Runner Plugin

**strataregula-doe-runner** is a batch experiment orchestrator plugin for the Strataregula ecosystem.

## Overview

DOE Runner is **NOT** a Design of Experiments design tool. It is a **batch experiment orchestrator** that executes predefined cases from CSV files and collects standardized metrics.

**Definition**: DOE Runner executes case sets defined in `cases.csv` deterministically in batch, collecting them into standardized `metrics.csv` (+ run logs).

## Key Features

### 🔄 Batch Processing
- Execute predefined experiment cases from CSV
- Deterministic execution with reproducible results
- Parallel execution with configurable workers
- Intelligent caching with `case_hash`

### 📊 Data Pipeline
- **Input**: `cases.csv` with case definitions
- **Output**: `metrics.csv` with standardized metrics
- **Logs**: JST timezone run logs in Markdown format

### 🔧 Execution Backends
- **Shell**: Execute shell commands
- **Dummy**: Testing/simulation backend
- **Simroute**: Integration with world-simulation (extras dependency)

### 📈 Quality Assurance
- Threshold validation with proper exit codes
- Comprehensive error handling and reporting
- Cache management for efficiency

## Installation

### From PyPI (when available)
```bash
pip install strataregula-doe-runner
```

### From GitHub (current)
```bash
pip install git+https://github.com/unizontech/strataregula-doe-runner.git
```

### Development Installation
```bash
git clone https://github.com/unizontech/strataregula-doe-runner.git
cd strataregula-doe-runner
pip install -e ".[dev]"
```

## Usage

### CLI Usage

```bash
# Basic execution
srd run --cases cases.csv --out metrics.csv

# With parallel execution
srd run --cases cases.csv --out metrics.csv --max-workers 4

# Force re-execution (ignore cache)
srd run --cases cases.csv --force

# Dry run validation
srd run --cases cases.csv --dry-run

# Verbose output
srd run --cases cases.csv --verbose
```

### Plugin Usage

```python
from strataregula_doe_runner.plugin import DOERunnerPlugin

# Initialize plugin
plugin = DOERunnerPlugin()

# Get plugin information
info = plugin.get_info()
print(f"Plugin: {info['name']} v{info['version']}")

# Execute cases
result = plugin.execute_cases(
    cases_path="cases.csv",
    metrics_path="metrics.csv",
    max_workers=2,
    verbose=True
)

if result['status'] == 'success':
    print(f"Execution completed with exit code: {result['exit_code']}")
    print(f"Stats: {result['stats']}")
else:
    print(f"Execution failed: {result['message']}")
```

## Cases CSV Format

### Required Columns
- `case_id`: Unique case identifier
- `backend`: Execution backend (`shell`/`dummy`/`simroute`)
- `cmd_template`: Command template with `{placeholders}`
- `timeout_s`: Timeout in seconds

### Optional Columns
- `seed`: Random seed for reproducibility
- `retries`: Number of retry attempts
- `resource_group`: Resource grouping for execution
- `expected_p95`, `expected_p99`: Expected metric values
- `threshold_p95`, `threshold_p99`: Threshold limits

### Example cases.csv
```csv
case_id,backend,cmd_template,timeout_s,seed,retries,resource_group,expected_p95,threshold_p95
test-01,shell,"echo 'p95=0.05 p99=0.08 throughput_rps=1000'",10,42,2,default,0.05,0.06
test-02,dummy,"dummy simulation",10,123,1,default,0.08,0.10
test-03,simroute,"python -m simroute_cli --seed {seed}",120,456,3,compute,0.10,0.12
```

## Metrics CSV Output

### Required Columns (Fixed Order)
```csv
case_id,status,run_seconds,p95,p99,throughput_rps,errors,ts_start,ts_end
```

### Status Values
- `OK`: Successful execution
- `FAIL`: Execution failed
- `TIMEOUT`: Execution timed out

### Additional Columns
- **Performance**: `cpu_util`, `mem_peak_mb`, `queue_depth_p95`, `latency_p50`
- **Parameters**: `param_*` (input case parameters transferred)
- **Extensions**: `ext_*`, `tag_*`, `note_*`

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All cases executed successfully, thresholds met |
| 2 | Execution completed but threshold violations detected |
| 3 | I/O error, invalid configuration, or execution failure |

## Environment Variables

- `RUN_LOG_DIR`: Directory for run logs (default: `docs/run`)
- `RUN_LOG_WRITE_COMPAT`: Compatibility mode flag (default: `0`)

## Plugin Integration

### Automatic Discovery
The plugin is automatically discoverable by Strataregula through entry points:

```toml
[project.entry-points."strataregula.plugins"]
"doe_runner" = "strataregula_doe_runner.plugin:DOERunnerPlugin"
```

### Plugin Commands
- `execute_cases`: Run cases from CSV
- `validate_cases`: Validate case format
- `get_cache_status`: Check cache status
- `clear_cache`: Clear execution cache
- `get_adapters`: List available adapters

## Architecture

### Independent Plugin Design
- No inheritance from BasePlugin
- Works standalone without Strataregula
- Discoverable through standard Python entry points
- Modular adapter system for extensibility

### Components
- **Runner**: Main execution engine
- **CaseExecutor**: Individual case execution management
- **CaseCache**: Result caching with case_hash
- **CSVHandler**: Deterministic CSV I/O
- **RunlogWriter**: JST timezone logging

### Backward Compatibility
- Package name: `strataregula_doe_runner`
- Legacy import: `sr_doe_runner` (deprecated with warnings)
- Repository: `strataregula-doe-runner`

## Examples

See the [examples directory](https://github.com/unizontech/strataregula-doe-runner/tree/main/examples) in the repository:

- `simple/`: Basic usage with shell and dummy backends
- `complex/`: Advanced configuration with all features
- `simroute/`: Integration with world-simulation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

Apache License 2.0 - see [LICENSE](https://github.com/unizontech/strataregula-doe-runner/blob/main/LICENSE) file.

## Links

- **Repository**: https://github.com/unizontech/strataregula-doe-runner
- **Issues**: https://github.com/unizontech/strataregula-doe-runner/issues
- **PyPI**: (coming soon)
- **Documentation**: This page and repository README