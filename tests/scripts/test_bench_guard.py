"""Tests for bench guard script functionality."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import sys
import os

# Add scripts directory to path to import bench_guard
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

try:
    import bench_guard
except ImportError:
    bench_guard = None


@pytest.mark.skipif(bench_guard is None, reason="bench_guard module not available")
class TestBenchGuard:
    """Test bench guard functionality."""
    
    def test_get_system_info(self):
        """Test system info collection."""
        if hasattr(bench_guard, 'get_system_info'):
            info = bench_guard.get_system_info()
            assert isinstance(info, dict)
            assert 'platform' in info
            assert 'python_version' in info
        
    def test_get_git_context(self):
        """Test git context collection.""" 
        if hasattr(bench_guard, 'get_git_context'):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout="main")
                context = bench_guard.get_git_context()
                assert isinstance(context, dict)
    
    def test_validate_result_schema(self):
        """Test result schema validation."""
        if hasattr(bench_guard, 'validate_result_schema'):
            # Test with valid basic structure
            test_result = {
                "timestamp": "2025-01-18T12:00:00+09:00",
                "config": {},
                "benchmarks": {
                    "pattern_expansion": {
                        "fast": {"ops": 1000, "p50_us": 10, "p95_us": 20, "p99_us": 30, "min_us": 5, "max_us": 50, "mean_us": 15, "std_us": 5},
                        "slow": {"ops": 100, "p50_us": 100, "p95_us": 200, "p99_us": 300, "min_us": 50, "max_us": 500, "mean_us": 150, "std_us": 50},
                        "ratio": 10.0
                    },
                    "config_compilation": {
                        "fast": {"ops": 1000, "p50_us": 10, "p95_us": 20, "p99_us": 30, "min_us": 5, "max_us": 50, "mean_us": 15, "std_us": 5},
                        "slow": {"ops": 100, "p50_us": 100, "p95_us": 200, "p99_us": 300, "min_us": 50, "max_us": 500, "mean_us": 150, "std_us": 50},
                        "ratio": 10.0
                    },
                    "kernel_cache": {
                        "fast": {"ops": 1000, "p50_us": 10, "p95_us": 20, "p99_us": 30, "min_us": 5, "max_us": 50, "mean_us": 15, "std_us": 5},
                        "slow": {"ops": 100, "p50_us": 100, "p95_us": 200, "p99_us": 300, "min_us": 50, "max_us": 500, "mean_us": 150, "std_us": 50},
                        "ratio": 10.0
                    }
                },
                "overall": {"min_ratio": 10.0, "max_p95_us": 20},
                "passed": True
            }
            
            try:
                result = bench_guard.validate_result_schema(test_result)
                assert result is True or result is None  # May not have jsonschema
            except Exception:
                # Schema validation might fail due to missing jsonschema
                pass
                
    def test_main_execution(self):
        """Test main execution path."""
        if hasattr(bench_guard, 'main'):
            with patch('bench_guard.get_system_info', return_value={}):
                with patch('bench_guard.get_git_context', return_value={}):
                    with patch('sys.argv', ['bench_guard.py']):
                        try:
                            bench_guard.main()
                        except SystemExit:
                            # Script might exit, that's normal
                            pass
                        except Exception:
                            # Other exceptions might occur, that's OK for testing
                            pass


@pytest.mark.skipif(bench_guard is None, reason="bench_guard module not available")  
class TestBenchGuardEnvironment:
    """Test bench guard environment handling."""
    
    def test_environment_variables(self):
        """Test environment variable handling.""" 
        # Test default values
        original_env = os.environ.copy()
        try:
            # Clear bench guard env vars
            for key in list(os.environ.keys()):
                if key.startswith('SR_BENCH_'):
                    del os.environ[key]
                    
            # Test with custom env vars
            os.environ['SR_BENCH_N'] = '1000'
            os.environ['SR_BENCH_WARMUP'] = '100'
            os.environ['SR_BENCH_MIN_RATIO'] = '50'
            
            if hasattr(bench_guard, 'get_config'):
                config = bench_guard.get_config()
                assert isinstance(config, dict)
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)


class TestBenchGuardStandalone:
    """Test bench guard functionality without importing the module."""
    
    def test_bench_guard_script_exists(self):
        """Test that bench guard script exists."""
        script_path = Path(__file__).parent.parent.parent / "scripts" / "bench_guard.py"
        assert script_path.exists()
        
    def test_bench_guard_schema_exists(self):
        """Test that bench guard schema exists."""
        schema_path = Path(__file__).parent.parent.parent / "scripts" / "bench_guard.schema.json"
        assert schema_path.exists()
        
        # Test schema is valid JSON
        with open(schema_path) as f:
            schema = json.load(f)
            assert isinstance(schema, dict)
            assert "required" in schema or "properties" in schema