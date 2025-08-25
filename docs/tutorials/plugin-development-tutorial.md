# Plugin Development Tutorial

Learn how to create your own Strataregula plugins with this step-by-step tutorial.

## Prerequisites

- Python 3.11 or higher
- Understanding of Python packages and entry points
- Familiarity with Strataregula basics

## Tutorial: Building a Log Analyzer Plugin

We'll create a log analyzer plugin that processes log files and extracts metrics.

### Step 1: Project Structure

Create the plugin project structure:

```
strataregula-log-analyzer/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── strataregula_log_analyzer/
│       ├── __init__.py
│       ├── plugin.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── analyzer.py
│       │   └── models.py
│       └── cli/
│           ├── __init__.py
│           └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_plugin.py
│   └── test_analyzer.py
└── examples/
    ├── sample.log
    └── analyze_logs.py
```

### Step 2: Package Configuration

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "strataregula-log-analyzer"
version = "0.1.0"
description = "Log analysis plugin for Strataregula ecosystem"
readme = "README.md"
license = {file = "LICENSE"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
requires-python = ">=3.11"
dependencies = [
    "click>=8.0.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "regex>=2023.0.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0"
]

[project.entry-points."strataregula.plugins"]
"log_analyzer" = "strataregula_log_analyzer.plugin:LogAnalyzerPlugin"

[project.scripts]
sla = "strataregula_log_analyzer.cli.main:main"
```

### Step 3: Data Models

Create `src/strataregula_log_analyzer/core/models.py`:

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel


@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    message: str
    source: str
    thread: Optional[str] = None
    extra: Optional[Dict[str, str]] = None


class AnalysisConfig(BaseModel):
    log_path: str
    pattern: str = r'(?P<timestamp>\S+\s+\S+)\s+(?P<level>\w+)\s+(?P<message>.*)'
    time_format: str = "%Y-%m-%d %H:%M:%S"
    output_path: Optional[str] = None
    include_metrics: List[str] = ["error_count", "warning_count", "total_entries"]


@dataclass
class AnalysisResult:
    total_entries: int
    error_count: int
    warning_count: int
    info_count: int
    debug_count: int
    time_range: tuple[datetime, datetime]
    top_errors: List[str]
    analysis_time: float
    
    def to_dict(self) -> Dict[str, any]:
        return {
            "total_entries": self.total_entries,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "debug_count": self.debug_count,
            "time_range": {
                "start": self.time_range[0].isoformat(),
                "end": self.time_range[1].isoformat()
            },
            "top_errors": self.top_errors,
            "analysis_time": self.analysis_time
        }
```

### Step 4: Core Analysis Engine

Create `src/strataregula_log_analyzer/core/analyzer.py`:

```python
import re
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Dict, Any

from .models import LogEntry, AnalysisConfig, AnalysisResult


class LogAnalyzer:
    """Core log analysis engine."""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.pattern = re.compile(config.pattern)
    
    def parse_log_entry(self, line: str) -> Optional[LogEntry]:
        """Parse a single log line into LogEntry."""
        match = self.pattern.match(line.strip())
        if not match:
            return None
        
        groups = match.groupdict()
        
        try:
            timestamp = datetime.strptime(
                groups.get('timestamp', ''), 
                self.config.time_format
            )
        except ValueError:
            timestamp = datetime.now()
        
        return LogEntry(
            timestamp=timestamp,
            level=groups.get('level', 'INFO').upper(),
            message=groups.get('message', ''),
            source=groups.get('source', 'unknown'),
            thread=groups.get('thread'),
            extra={k: v for k, v in groups.items() 
                  if k not in ['timestamp', 'level', 'message', 'source', 'thread']}
        )
    
    def read_log_file(self) -> Generator[LogEntry, None, None]:
        """Read and parse log file entries."""
        log_path = Path(self.config.log_path)
        
        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_path}")
        
        with open(log_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = self.parse_log_entry(line)
                    if entry:
                        yield entry
                except Exception as e:
                    print(f"Error parsing line {line_num}: {e}")
                    continue
    
    def analyze(self) -> AnalysisResult:
        """Perform log analysis."""
        start_time = time.time()
        
        level_counts = defaultdict(int)
        error_messages = Counter()
        timestamps = []
        total_entries = 0
        
        for entry in self.read_log_file():
            total_entries += 1
            level_counts[entry.level] += 1
            timestamps.append(entry.timestamp)
            
            if entry.level == 'ERROR':
                error_messages[entry.message] += 1
        
        analysis_time = time.time() - start_time
        
        # Calculate time range
        time_range = (min(timestamps), max(timestamps)) if timestamps else (
            datetime.now(), datetime.now()
        )
        
        # Get top errors
        top_errors = [msg for msg, count in error_messages.most_common(10)]
        
        return AnalysisResult(
            total_entries=total_entries,
            error_count=level_counts['ERROR'],
            warning_count=level_counts['WARNING'],
            info_count=level_counts['INFO'],
            debug_count=level_counts['DEBUG'],
            time_range=time_range,
            top_errors=top_errors,
            analysis_time=analysis_time
        )
    
    def export_results(self, result: AnalysisResult, format: str = "json") -> str:
        """Export analysis results to specified format."""
        import json
        import csv
        from io import StringIO
        
        if format.lower() == "json":
            return json.dumps(result.to_dict(), indent=2)
        
        elif format.lower() == "csv":
            output = StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(["Metric", "Value"])
            
            # Write data
            data = result.to_dict()
            for key, value in data.items():
                if key == "time_range":
                    writer.writerow(["start_time", value["start"]])
                    writer.writerow(["end_time", value["end"]])
                elif key == "top_errors":
                    for i, error in enumerate(value[:5], 1):
                        writer.writerow([f"top_error_{i}", error])
                else:
                    writer.writerow([key, value])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format}")
```

### Step 5: Plugin Implementation

Create `src/strataregula_log_analyzer/plugin.py`:

```python
from typing import Dict, Any
from pathlib import Path

from .core.analyzer import LogAnalyzer
from .core.models import AnalysisConfig


class LogAnalyzerPlugin:
    """Log analyzer plugin for Strataregula ecosystem."""
    
    # Plugin metadata
    name = "log_analyzer"
    version = "0.1.0"
    description = "Analyze log files and extract metrics"
    author = "Your Name"
    
    def __init__(self):
        """Initialize plugin."""
        self._analyzer = None
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "supported_commands": [
                "analyze_log",
                "validate_log",
                "export_results",
                "get_log_stats"
            ]
        }
    
    def analyze_log(self, **kwargs) -> Dict[str, Any]:
        """Analyze log file and return metrics."""
        try:
            # Validate required parameters
            log_path = kwargs.get('log_path')
            if not log_path:
                return {
                    'status': 'error',
                    'message': 'log_path parameter is required'
                }
            
            # Create configuration
            config = AnalysisConfig(
                log_path=log_path,
                pattern=kwargs.get('pattern', r'(?P<timestamp>\S+\s+\S+)\s+(?P<level>\w+)\s+(?P<message>.*)'),
                time_format=kwargs.get('time_format', "%Y-%m-%d %H:%M:%S"),
                output_path=kwargs.get('output_path'),
                include_metrics=kwargs.get('include_metrics', ["error_count", "warning_count", "total_entries"])
            )
            
            # Perform analysis
            analyzer = LogAnalyzer(config)
            result = analyzer.analyze()
            
            # Export if output path specified
            if config.output_path:
                format = kwargs.get('format', 'json')
                exported = analyzer.export_results(result, format)
                
                with open(config.output_path, 'w') as f:
                    f.write(exported)
            
            return {
                'status': 'success',
                'result': result.to_dict(),
                'output_path': config.output_path
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def validate_log(self, **kwargs) -> Dict[str, Any]:
        """Validate log file format."""
        try:
            log_path = kwargs.get('log_path')
            if not log_path:
                return {
                    'status': 'error',
                    'message': 'log_path parameter is required'
                }
            
            log_file = Path(log_path)
            if not log_file.exists():
                return {
                    'status': 'error',
                    'message': f'Log file not found: {log_path}'
                }
            
            # Quick validation by parsing first few lines
            config = AnalysisConfig(
                log_path=log_path,
                pattern=kwargs.get('pattern', r'(?P<timestamp>\S+\s+\S+)\s+(?P<level>\w+)\s+(?P<message>.*)')
            )
            
            analyzer = LogAnalyzer(config)
            valid_entries = 0
            total_entries = 0
            
            with open(log_path, 'r') as f:
                for i, line in enumerate(f):
                    if i >= 100:  # Sample first 100 lines
                        break
                    total_entries += 1
                    if analyzer.parse_log_entry(line):
                        valid_entries += 1
            
            validation_rate = valid_entries / total_entries if total_entries > 0 else 0
            
            return {
                'status': 'success',
                'valid': validation_rate > 0.8,  # 80% threshold
                'validation_rate': validation_rate,
                'sample_size': total_entries
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_log_stats(self, **kwargs) -> Dict[str, Any]:
        """Get basic log file statistics."""
        try:
            log_path = kwargs.get('log_path')
            if not log_path:
                return {
                    'status': 'error',
                    'message': 'log_path parameter is required'
                }
            
            log_file = Path(log_path)
            if not log_file.exists():
                return {
                    'status': 'error',
                    'message': f'Log file not found: {log_path}'
                }
            
            # Get file stats
            stats = log_file.stat()
            line_count = sum(1 for _ in open(log_path, 'r'))
            
            return {
                'status': 'success',
                'stats': {
                    'file_size': stats.st_size,
                    'line_count': line_count,
                    'modified_time': stats.st_mtime,
                    'file_path': str(log_file.absolute())
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }


# Plugin factory function
def create_plugin():
    """Factory function to create plugin instance."""
    return LogAnalyzerPlugin()
```

### Step 6: CLI Interface

Create `src/strataregula_log_analyzer/cli/main.py`:

```python
import click
import json
from pathlib import Path

from ..plugin import LogAnalyzerPlugin


@click.group()
@click.version_option()
def main():
    """Strataregula Log Analyzer CLI"""
    pass


@main.command()
@click.argument('log_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path')
@click.option('--format', '-f', default='json', 
              type=click.Choice(['json', 'csv']), 
              help='Output format')
@click.option('--pattern', '-p', help='Custom log parsing pattern')
@click.option('--time-format', help='Timestamp format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def analyze(log_file, output, format, pattern, time_format, verbose):
    """Analyze log file and extract metrics."""
    plugin = LogAnalyzerPlugin()
    
    kwargs = {
        'log_path': log_file,
        'output_path': output,
        'format': format
    }
    
    if pattern:
        kwargs['pattern'] = pattern
    if time_format:
        kwargs['time_format'] = time_format
    
    if verbose:
        click.echo(f"Analyzing log file: {log_file}")
        click.echo(f"Output format: {format}")
    
    result = plugin.analyze_log(**kwargs)
    
    if result['status'] == 'success':
        if verbose:
            click.echo("Analysis completed successfully!")
            click.echo(f"Total entries: {result['result']['total_entries']}")
            click.echo(f"Errors: {result['result']['error_count']}")
            click.echo(f"Warnings: {result['result']['warning_count']}")
        
        if not output:
            # Print to console
            if format == 'json':
                click.echo(json.dumps(result['result'], indent=2))
            else:
                click.echo("Use --output option for CSV format")
        else:
            click.echo(f"Results exported to: {output}")
    else:
        click.echo(f"Analysis failed: {result['message']}", err=True)


@main.command()
@click.argument('log_file', type=click.Path(exists=True))
@click.option('--pattern', '-p', help='Custom log parsing pattern')
def validate(log_file, pattern):
    """Validate log file format."""
    plugin = LogAnalyzerPlugin()
    
    kwargs = {
        'log_path': log_file
    }
    
    if pattern:
        kwargs['pattern'] = pattern
    
    result = plugin.validate_log(**kwargs)
    
    if result['status'] == 'success':
        if result['valid']:
            click.echo("✅ Log file format is valid")
        else:
            click.echo("❌ Log file format validation failed")
        
        click.echo(f"Validation rate: {result['validation_rate']:.2%}")
        click.echo(f"Sample size: {result['sample_size']} lines")
    else:
        click.echo(f"Validation failed: {result['message']}", err=True)


@main.command()
@click.argument('log_file', type=click.Path(exists=True))
def stats(log_file):
    """Get basic log file statistics."""
    plugin = LogAnalyzerPlugin()
    
    result = plugin.get_log_stats(log_path=log_file)
    
    if result['status'] == 'success':
        stats = result['stats']
        click.echo("📊 Log File Statistics")
        click.echo("=" * 20)
        click.echo(f"File size: {stats['file_size']:,} bytes")
        click.echo(f"Line count: {stats['line_count']:,}")
        click.echo(f"File path: {stats['file_path']}")
    else:
        click.echo(f"Failed to get statistics: {result['message']}", err=True)


if __name__ == '__main__':
    main()
```

### Step 7: Tests

Create `tests/test_plugin.py`:

```python
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from strataregula_log_analyzer.plugin import LogAnalyzerPlugin


@pytest.fixture
def sample_log():
    """Create a sample log file for testing."""
    content = """2025-08-25 10:00:01 INFO Starting application
2025-08-25 10:00:02 DEBUG Loading configuration
2025-08-25 10:00:03 WARNING Configuration file not found, using defaults
2025-08-25 10:00:04 ERROR Failed to connect to database
2025-08-25 10:00:05 INFO Application started successfully
2025-08-25 10:00:06 ERROR Database connection timeout
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(content)
        return f.name


def test_plugin_info():
    """Test plugin information."""
    plugin = LogAnalyzerPlugin()
    info = plugin.get_info()
    
    assert info['name'] == 'log_analyzer'
    assert 'analyze_log' in info['supported_commands']
    assert 'version' in info


def test_analyze_log(sample_log):
    """Test log analysis functionality."""
    plugin = LogAnalyzerPlugin()
    
    result = plugin.analyze_log(log_path=sample_log)
    
    assert result['status'] == 'success'
    assert 'result' in result
    
    analysis = result['result']
    assert analysis['total_entries'] == 6
    assert analysis['error_count'] == 2
    assert analysis['warning_count'] == 1
    assert analysis['info_count'] == 2


def test_validate_log(sample_log):
    """Test log validation."""
    plugin = LogAnalyzerPlugin()
    
    result = plugin.validate_log(log_path=sample_log)
    
    assert result['status'] == 'success'
    assert result['valid'] is True
    assert result['validation_rate'] > 0.8


def test_get_log_stats(sample_log):
    """Test log statistics."""
    plugin = LogAnalyzerPlugin()
    
    result = plugin.get_log_stats(log_path=sample_log)
    
    assert result['status'] == 'success'
    assert 'stats' in result
    assert result['stats']['line_count'] == 6


def test_missing_log_file():
    """Test handling of missing log file."""
    plugin = LogAnalyzerPlugin()
    
    result = plugin.analyze_log(log_path='nonexistent.log')
    
    assert result['status'] == 'error'
    assert 'not found' in result['message'].lower()


def test_export_results(sample_log):
    """Test results export."""
    plugin = LogAnalyzerPlugin()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
    
    result = plugin.analyze_log(
        log_path=sample_log,
        output_path=output_path,
        format='json'
    )
    
    assert result['status'] == 'success'
    assert Path(output_path).exists()
    
    # Verify exported content
    with open(output_path, 'r') as f:
        import json
        exported_data = json.load(f)
        assert exported_data['total_entries'] == 6


@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup temporary files after tests."""
    yield
    # Cleanup code here if needed
```

### Step 8: Example Usage

Create `examples/analyze_logs.py`:

```python
#!/usr/bin/env python3
"""
Example usage of the Log Analyzer plugin.
"""

from strataregula_log_analyzer.plugin import LogAnalyzerPlugin


def main():
    # Initialize plugin
    plugin = LogAnalyzerPlugin()
    
    # Get plugin info
    info = plugin.get_info()
    print(f"Using plugin: {info['name']} v{info['version']}")
    
    # Analyze sample log
    log_file = "sample.log"
    
    # First validate the log
    print("\n🔍 Validating log file...")
    validation_result = plugin.validate_log(log_path=log_file)
    
    if validation_result['status'] == 'success' and validation_result['valid']:
        print("✅ Log file is valid")
        
        # Perform analysis
        print("\n📊 Analyzing log file...")
        analysis_result = plugin.analyze_log(
            log_path=log_file,
            output_path="analysis_results.json",
            format="json"
        )
        
        if analysis_result['status'] == 'success':
            result = analysis_result['result']
            
            print("\n📈 Analysis Results:")
            print(f"Total entries: {result['total_entries']}")
            print(f"Errors: {result['error_count']}")
            print(f"Warnings: {result['warning_count']}")
            print(f"Info: {result['info_count']}")
            print(f"Debug: {result['debug_count']}")
            print(f"Analysis time: {result['analysis_time']:.3f}s")
            
            if result['top_errors']:
                print("\n🚨 Top Errors:")
                for i, error in enumerate(result['top_errors'][:5], 1):
                    print(f"  {i}. {error}")
        else:
            print(f"❌ Analysis failed: {analysis_result['message']}")
    else:
        print("❌ Log file validation failed")


if __name__ == "__main__":
    main()
```

### Step 9: Installation and Testing

Install the plugin in development mode:

```bash
cd strataregula-log-analyzer
pip install -e ".[dev]"
```

Run tests:

```bash
pytest tests/ -v
```

Test CLI:

```bash
# Create a sample log file
echo "2025-08-25 10:00:01 INFO Test message
2025-08-25 10:00:02 ERROR Test error" > test.log

# Analyze the log
sla analyze test.log --verbose

# Validate the log
sla validate test.log

# Get stats
sla stats test.log
```

Test as a plugin:

```python
from strataregula_log_analyzer.plugin import LogAnalyzerPlugin

plugin = LogAnalyzerPlugin()
result = plugin.analyze_log(log_path="test.log")
print(result)
```

### Step 10: Distribution

Create a README.md and publish to PyPI:

```bash
# Build the package
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## Key Concepts Learned

1. **Independent Architecture**: Plugin works standalone without Strataregula
2. **Entry Points**: Automatic discovery through Python entry points
3. **Consistent Interface**: Standard plugin methods and return formats
4. **Error Handling**: Comprehensive error handling and reporting
5. **CLI Integration**: Standalone CLI that can also work as a plugin
6. **Testing**: Comprehensive test suite with fixtures
7. **Documentation**: Clear examples and usage patterns

## Next Steps

- Add more analysis features (regex patterns, custom metrics)
- Implement real-time log monitoring
- Add support for multiple log formats
- Create web dashboard for results visualization
- Integrate with monitoring systems (Prometheus, Grafana)

This tutorial demonstrates the complete lifecycle of creating a Strataregula plugin following best practices and architectural patterns.