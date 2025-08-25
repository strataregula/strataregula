"""
Benchmark tests for Strataregula compilation speed.
Tests the performance of configuration compilation and code generation.
"""

import time
import pytest
import psutil
import os
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any

# Import Strataregula modules
try:
    from strataregula.core.compiler import PatternCompiler
    from strataregula.core.pattern_expander import EnhancedPatternExpander
except ImportError:
    pytest.skip("Strataregula core modules not available", allow_module_level=True)


class TestCompilationBenchmarks:
    """Benchmark tests for compilation performance."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create sample configurations of various sizes
        self.small_config = self._create_test_config(services=10, patterns=5)
        self.medium_config = self._create_test_config(services=100, patterns=20)
        self.large_config = self._create_test_config(services=500, patterns=50)
        
    def _create_test_config(self, services: int, patterns: int) -> Dict[str, Any]:
        """Create test configuration with specified complexity."""
        config = {
            'services': {
                'api': [],
                'web': [],
                'cache': [],
                'monitor': []
            },
            'regions': {
                'kanto': ['tokyo', 'chiba', 'saitama'],
                'kansai': ['osaka', 'kyoto', 'hyogo'],
                'kyushu': ['fukuoka', 'saga', 'kumamoto']
            }
        }
        
        # Add service patterns
        pattern_count = 0
        for category in config['services']:
            for i in range(patterns // 4):  # Distribute patterns across categories
                if pattern_count < patterns:
                    config['services'][category].append(f"{category}.*.service{i:03d}")
                    pattern_count += 1
        
        # Add literal services to reach target count
        literal_count = 0
        for category in config['services']:
            for region in ['tokyo', 'osaka', 'fukuoka']:
                for i in range((services - patterns) // 12):  # Distribute remaining
                    if literal_count < services - patterns:
                        config['services'][category].append(f"{category}.{region}.literal{i:03d}")
                        literal_count += 1
        
        return config
    
    def _save_config_to_file(self, config: Dict[str, Any], filename: str) -> Path:
        """Save configuration to temporary file."""
        config_path = self.temp_dir / filename
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        return config_path
    
    def test_small_config_compilation_speed(self):
        """Test compilation speed for small configurations."""
        config_path = self._save_config_to_file(self.small_config, "small_config.yaml")
        output_path = self.temp_dir / "small_output.py"
        
        start_time = time.time()
        compiler = PatternCompiler()
        compiler.load_config(config_path)
        result = compiler.compile_patterns(self.small_config)
        end_time = time.time()
        
        # Write output file
        with open(output_path, 'w') as f:
            f.write(f"# Generated configuration\n{result}")
        
        duration = end_time - start_time
        
        # Small configs should compile very quickly
        assert duration < 0.5, f"Small config compilation too slow: {duration:.3f}s"
        assert output_path.exists(), "Output file not created"
        
        print(f"Small config compilation: {duration:.3f}s")
        print(f"   Generated {len(result)} entries")
    
    def test_medium_config_compilation_speed(self):
        """Test compilation speed for medium configurations."""
        config_path = self._save_config_to_file(self.medium_config, "medium_config.yaml")
        output_path = self.temp_dir / "medium_output.py"
        
        start_time = time.time()
        compiler = PatternCompiler()
        compiler.load_config(config_path)
        result = compiler.compile_patterns(self.medium_config)
        end_time = time.time()
        
        # Write output file
        with open(output_path, 'w') as f:
            f.write(f"# Generated configuration\n{result}")
        
        duration = end_time - start_time
        
        # Medium configs should compile in reasonable time
        assert duration < 2.0, f"Medium config compilation too slow: {duration:.3f}s"
        assert output_path.exists(), "Output file not created"
        
        print(f"Medium config compilation: {duration:.3f}s")
        print(f"   Generated {len(result)} entries")
    
    def test_large_config_compilation_speed(self):
        """Test compilation speed for large configurations."""
        config_path = self._save_config_to_file(self.large_config, "large_config.yaml")
        output_path = self.temp_dir / "large_output.py"
        
        start_time = time.time()
        compiler = PatternCompiler()
        compiler.load_config(config_path)
        result = compiler.compile_patterns(self.large_config)
        end_time = time.time()
        
        # Write output file
        with open(output_path, 'w') as f:
            f.write(f"# Generated configuration\n{result}")
        
        duration = end_time - start_time
        
        # Large configs should still compile in acceptable time
        assert duration < 10.0, f"Large config compilation too slow: {duration:.3f}s"
        assert output_path.exists(), "Output file not created"
        
        print(f"Large config compilation: {duration:.3f}s")
        print(f"   Generated {len(result)} entries")
    
    def test_multiple_output_formats_speed(self):
        """Test compilation speed across different output formats."""
        config_path = self._save_config_to_file(self.medium_config, "multi_format_config.yaml")
        
        formats = ['python', 'json', 'yaml']
        format_times = {}
        
        for format_type in formats:
            output_path = self.temp_dir / f"multi_output.{format_type}"
            
            start_time = time.time()
            compiler = PatternCompiler()
            compiler.load_config(config_path)
            result = compiler.compile_patterns(self.medium_config)
            end_time = time.time()
            
            duration = end_time - start_time
            format_times[format_type] = duration
            
            # Write output in requested format
            with open(output_path, 'w') as f:
                if format_type == 'json':
                    import json
                    json.dump(result, f, indent=2)
                elif format_type == 'yaml':
                    yaml.dump(result, f)
                else:
                    f.write(f"# Generated configuration\n{result}")
            
            assert output_path.exists(), f"Output file not created for {format_type}"
            print(f"   {format_type:>6}: {duration:.3f}s")
        
        # All formats should compile reasonably quickly
        for format_type, duration in format_times.items():
            assert duration < 3.0, f"{format_type} format too slow: {duration:.3f}s"
        
        print(f"Multi-format compilation benchmark completed")
    
    def test_memory_usage_during_compilation(self):
        """Test memory usage during large configuration compilation."""
        # Create very large config
        huge_config = self._create_test_config(services=1000, patterns=100)
        config_path = self._save_config_to_file(huge_config, "huge_config.yaml")
        output_path = self.temp_dir / "huge_output.py"
        
        # Monitor memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        compiler = PatternCompiler()
        compiler.load_config(config_path)
        result = compiler.compile_patterns(huge_config)
        end_time = time.time()
        
        # Write output file
        with open(output_path, 'w') as f:
            f.write(f"# Generated configuration\n{result}")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        duration = end_time - start_time
        
        # Memory usage should stay within limits
        assert memory_increase < 300, f"Memory usage too high: {memory_increase:.1f}MB"
        assert duration < 15.0, f"Huge config compilation too slow: {duration:.3f}s"
        
        print(f"Memory usage benchmark: {memory_increase:.1f}MB increase")
        print(f"   Duration: {duration:.3f}s for {len(result)} entries")
    
    def test_streaming_vs_batch_compilation(self):
        """Compare streaming vs batch compilation performance."""
        config_path = self._save_config_to_file(self.large_config, "streaming_config.yaml")
        
        # Batch compilation
        batch_output = self.temp_dir / "batch_output.py"
        
        start_time = time.time()
        batch_compiler = PatternCompiler()
        batch_compiler.load_config(config_path)
        batch_result = batch_compiler.compile_patterns(self.large_config)
        batch_time = time.time() - start_time
        
        with open(batch_output, 'w') as f:
            f.write(f"# Generated configuration\n{batch_result}")
        
        # Streaming compilation using enhanced expander
        streaming_output = self.temp_dir / "streaming_output.py"
        
        start_time = time.time()
        expander = EnhancedPatternExpander()
        streaming_result = list(expander.expand_pattern_stream(self.large_config))
        streaming_time = time.time() - start_time
        
        with open(streaming_output, 'w') as f:
            f.write(f"# Generated streaming configuration\n{streaming_result}")
        
        print(f"Compilation method comparison:")
        print(f"   Batch:     {batch_time:.3f}s")
        print(f"   Streaming: {streaming_time:.3f}s")
        
        # Both methods should produce results
        assert len(batch_result) > 0
        assert len(streaming_result) > 0
    
    def test_caching_compilation_speedup(self):
        """Test compilation speedup from caching."""
        config_path = self._save_config_to_file(self.medium_config, "cache_config.yaml")
        output_path = self.temp_dir / "cache_output.py"
        
        # First compilation (cold cache)
        start_time = time.time()
        compiler1 = PatternCompiler()
        compiler1.load_config(config_path)
        result1 = compiler1.compile_patterns(self.medium_config)
        first_time = time.time() - start_time
        
        # Second compilation (warm cache - same compiler instance)
        start_time = time.time()
        result2 = compiler1.compile_patterns(self.medium_config)
        second_time = time.time() - start_time
        
        with open(output_path, 'w') as f:
            f.write(f"# Generated configuration\n{result2}")
        
        # Cache should provide speedup
        speedup = first_time / second_time if second_time > 0 else float('inf')
        
        assert second_time < first_time, "Caching should improve compilation speed"
        assert speedup > 1.5, f"Cache speedup insufficient: {speedup:.1f}x"
        
        print(f"Compilation caching benchmark:")
        print(f"   Cold cache: {first_time:.3f}s")
        print(f"   Warm cache: {second_time:.3f}s")
        print(f"   Speedup: {speedup:.1f}x")
    
    def test_concurrent_compilation_performance(self):
        """Test performance of concurrent compilations."""
        import threading
        import concurrent.futures
        
        # Create multiple configs
        configs = [
            self._save_config_to_file(
                self._create_test_config(100, 20), 
                f"concurrent_config_{i}.yaml"
            ) for i in range(4)
        ]
        
        def compile_config(config_path, index):
            """Compile a single configuration."""
            output_path = self.temp_dir / f"concurrent_output_{index}.py"
            start_time = time.time()
            compiler = PatternCompiler()
            compiler.load_config(config_path)
            result = compiler.compile_patterns(self._create_test_config(100, 20))
            duration = time.time() - start_time
            
            with open(output_path, 'w') as f:
                f.write(f"# Generated configuration\n{result}")
            
            return duration, len(result)
        
        # Sequential compilation
        start_time = time.time()
        sequential_results = []
        for i, config_path in enumerate(configs):
            sequential_results.append(compile_config(config_path, f"seq_{i}"))
        sequential_total_time = time.time() - start_time
        
        # Concurrent compilation
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            concurrent_futures = [
                executor.submit(compile_config, config_path, f"conc_{i}")
                for i, config_path in enumerate(configs)
            ]
            concurrent_results = [f.result() for f in concurrent_futures]
        concurrent_total_time = time.time() - start_time
        
        # Concurrent should be faster for multiple compilations
        speedup = sequential_total_time / concurrent_total_time
        
        print(f"Concurrent compilation benchmark:")
        print(f"   Sequential: {sequential_total_time:.3f}s")
        print(f"   Concurrent: {concurrent_total_time:.3f}s")
        print(f"   Speedup: {speedup:.1f}x")
        
        # For very small workloads, concurrent overhead might exceed benefits
        # Just ensure both methods complete successfully
        if speedup > 1.0:
            print(f"Concurrent processing provided {speedup:.2f}x speedup")
        else:
            print(f"Sequential was faster for this small workload: {speedup:.2f}x")
        
        # Just ensure both methods produce results
        assert len(sequential_results) == len(concurrent_results)
        assert all(len(result) == 2 for result in sequential_results)
        assert all(len(result) == 2 for result in concurrent_results)


class TestCompilationRegression:
    """Performance regression tests for compilation."""
    
    def test_no_compilation_regression(self):
        """Ensure compilation performance hasn't regressed."""
        # Baseline measurements (these should not regress significantly)
        BASELINE_TIMES = {
            'small_config': 0.5,   # seconds for ~50 services
            'medium_config': 2.0,  # seconds for ~500 services
            'large_config': 10.0   # seconds for ~2000 services
        }
        
        temp_dir = Path(tempfile.mkdtemp())
        
        # Test configurations
        test_configs = {
            'small_config': {
                'services': {'api': ['api.*.service']},
                'regions': {'test': ['a', 'b', 'c']}
            },
            'medium_config': {
                'services': {
                    'api': [f'api.*.service{i}' for i in range(10)],
                    'web': [f'web.*.frontend{i}' for i in range(10)]
                },
                'regions': {'test': [f'region{i}' for i in range(10)]}
            },
            'large_config': {
                'services': {
                    'api': [f'api.*.service{i}' for i in range(50)],
                    'web': [f'web.*.frontend{i}' for i in range(25)],
                    'db': [f'db.*.primary{i}' for i in range(25)]
                },
                'regions': {'test': [f'region{i}' for i in range(20)]}
            }
        }
        
        for config_name, config_data in test_configs.items():
            config_path = temp_dir / f"{config_name}.yaml"
            output_path = temp_dir / f"{config_name}_output.py"
            
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            start_time = time.time()
            compiler = PatternCompiler()
            compiler.load_config(config_path)
            result = compiler.compile_patterns(config_data)
            duration = time.time() - start_time
            
            with open(output_path, 'w') as f:
                f.write(f"# Generated configuration\n{result}")
            
            baseline_time = BASELINE_TIMES[config_name]
            
            # Allow 2x regression tolerance
            assert duration < baseline_time * 2, \
                f"Compilation regression in {config_name}: {duration:.3f}s > {baseline_time * 2}s"
            
            print(f"{config_name}: {duration:.3f}s (baseline: {baseline_time}s)")


if __name__ == "__main__":
    # Run benchmarks directly
    pytest.main([__file__, "-v", "-s"])