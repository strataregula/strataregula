"""
Performance tests for strataregula with large-scale data processing.
These tests verify memory efficiency and processing speed requirements.
"""

import json
import os
import psutil
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List
import pytest
import yaml

from strataregula.core.config_compiler import ConfigCompiler, CompilationConfig
from strataregula.core.pattern_expander import EnhancedPatternExpander, StreamingPatternProcessor


class TestLargeScalePerformance:
    """Performance tests with large datasets."""
    
    def create_large_configuration(self, temp_dir: Path, num_patterns: int) -> tuple:
        """Create large-scale configuration for performance testing."""
        
        # Generate large traffic configuration
        traffic_data = {'service_times': {}}
        
        # Base service types
        service_types = [
            'edge', 'service-hub', 'corebrain', 'monitor', 'backup',
            'cache', 'database', 'queue', 'analytics', 'processing'
        ]
        
        # Generate patterns
        pattern_count = 0
        for service_type in service_types:
            # Single wildcard patterns
            for i in range(num_patterns // (len(service_types) * 3)):
                pattern = f'{service_type}.pattern_{i}.*'
                traffic_data['service_times'][pattern] = 0.1 + (i * 0.001) % 1.0
                pattern_count += 1
            
            # Double wildcard patterns  
            for i in range(num_patterns // (len(service_types) * 3)):
                pattern = f'{service_type}.*.service_{i}'
                traffic_data['service_times'][pattern] = 0.05 + (i * 0.0005) % 0.5
                pattern_count += 1
                
            # Triple wildcard patterns
            for i in range(num_patterns // (len(service_types) * 3)):
                pattern = f'{service_type}.*.*.level_{i}'
                traffic_data['service_times'][pattern] = 0.15 + (i * 0.002) % 0.8
                pattern_count += 1
        
        # Add direct mappings (no wildcards)
        for i in range(min(100, num_patterns // 10)):
            direct_service = f'direct.service_{i}'
            traffic_data['service_times'][direct_service] = 0.01 + (i * 0.0001)
        
        # Create comprehensive prefecture hierarchy
        prefectures_data = self.create_comprehensive_hierarchy()
        
        traffic_file = temp_dir / f'large_traffic_{num_patterns}.yaml'
        prefectures_file = temp_dir / f'hierarchy_{num_patterns}.yaml'
        
        with open(traffic_file, 'w') as f:
            yaml.dump(traffic_data, f, default_flow_style=False)
        with open(prefectures_file, 'w') as f:
            yaml.dump(prefectures_data, f, default_flow_style=False)
            
        return traffic_file, prefectures_file, pattern_count

    def create_comprehensive_hierarchy(self) -> Dict[str, Any]:
        """Create comprehensive hierarchy for realistic expansion."""
        return {
            'prefectures': {
                # Kanto region (7 prefectures)
                'tokyo': 'kanto', 'kanagawa': 'kanto', 'saitama': 'kanto',
                'chiba': 'kanto', 'ibaraki': 'kanto', 'tochigi': 'kanto', 'gunma': 'kanto',
                
                # Kansai region (6 prefectures) 
                'osaka': 'kansai', 'kyoto': 'kansai', 'hyogo': 'kansai',
                'nara': 'kansai', 'wakayama': 'kansai', 'shiga': 'kansai',
                
                # Chubu region (9 prefectures)
                'aichi': 'chubu', 'shizuoka': 'chubu', 'gifu': 'chubu',
                'nagano': 'chubu', 'yamanashi': 'chubu', 'niigata': 'chubu',
                'toyama': 'chubu', 'ishikawa': 'chubu', 'fukui': 'chubu',
                
                # Other regions (remaining 25 prefectures for total of 47)
                'fukuoka': 'kyushu', 'saga': 'kyushu', 'nagasaki': 'kyushu', 'kumamoto': 'kyushu',
                'oita': 'kyushu', 'miyazaki': 'kyushu', 'kagoshima': 'kyushu', 'okinawa': 'kyushu',
                
                'hokkaido': 'hokkaido',
                
                'aomori': 'tohoku', 'iwate': 'tohoku', 'miyagi': 'tohoku',
                'akita': 'tohoku', 'yamagata': 'tohoku', 'fukushima': 'tohoku',
                
                'tottori': 'chugoku', 'shimane': 'chugoku', 'okayama': 'chugoku',
                'hiroshima': 'chugoku', 'yamaguchi': 'chugoku',
                
                'tokushima': 'shikoku', 'kagawa': 'shikoku', 'ehime': 'shikoku', 'kochi': 'shikoku',
                
                # Additional test prefectures
                'test_pref_1': 'kanto', 'test_pref_2': 'kansai', 'test_pref_3': 'chubu',
                'test_pref_4': 'kyushu', 'test_pref_5': 'hokkaido'
            },
            
            'regions': [
                'kanto', 'kansai', 'chubu', 'kyushu', 'hokkaido', 
                'tohoku', 'chugoku', 'shikoku'
            ],
            
            'services': [
                'edge', 'service-hub', 'corebrain', 'gateway', 'api', 'web',
                'monitor', 'backup', 'cache', 'database', 'queue', 'analytics',
                'processing', 'storage', 'logging', 'security', 'proxy', 'balancer'
            ],
            
            'roles': [
                'gateway', 'api', 'web', 'processor', 'analytics', 'storage',
                'cache', 'backup', 'monitor', 'critical', 'daily', 'hot',
                'primary', 'replica', 'main', 'retry', 'worker', 'master'
            ],
            
            'pattern_rules': {
                'edge.*.*': {
                    'data_source': 'prefectures',
                    'template': 'edge.{prefecture}.{role}',
                    'priority': 100
                },
                'service-hub.*.*': {
                    'data_source': 'regions', 
                    'template': 'service-hub.{region}.{service}',
                    'priority': 75
                },
                'corebrain.*.*': {
                    'data_source': 'regions',
                    'template': 'corebrain.{region}.{service}',
                    'priority': 60
                },
                'monitor.*.*.*': {
                    'data_source': 'prefectures',
                    'template': 'monitor.{prefecture}.{service}.{level}',
                    'priority': 30
                }
            }
        }

    @pytest.mark.performance
    def test_1000_pattern_compilation_performance(self):
        """Test performance with 1000 patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create large configuration
            traffic_file, prefectures_file, pattern_count = self.create_large_configuration(
                temp_path, 1000
            )
            output_file = temp_path / 'output_1000.py'
            
            # Monitor memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Time the compilation
            start_time = time.time()
            
            compiler = ConfigCompiler(CompilationConfig(max_memory_mb=300))
            result = compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            end_time = time.time()
            compilation_time = end_time - start_time
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = final_memory - initial_memory
            
            # Verify success
            assert output_file.exists()
            assert len(result) > 0
            
            # Performance requirements
            assert compilation_time < 30  # Max 30 seconds
            assert memory_used < 300      # Max 300MB additional memory
            
            # Verify output quality
            content = output_file.read_text()
            assert 'COMPONENT_MAPPING' in content
            assert len(content) > 10000  # Substantial generated code

    @pytest.mark.performance  
    def test_5000_pattern_compilation_performance(self):
        """Test performance with 5000 patterns - stress test."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create very large configuration
            traffic_file, prefectures_file, pattern_count = self.create_large_configuration(
                temp_path, 5000
            )
            output_file = temp_path / 'output_5000.py'
            
            # Monitor memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Time the compilation with memory constraints
            start_time = time.time()
            
            config = CompilationConfig(
                max_memory_mb=500,  # Higher limit for stress test
                chunk_size=512      # Smaller chunks for memory efficiency
            )
            compiler = ConfigCompiler(config)
            
            result = compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            end_time = time.time()
            compilation_time = end_time - start_time
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = final_memory - initial_memory
            
            # Verify success
            assert output_file.exists()
            assert len(result) > 0
            
            # Stress test requirements (more lenient)
            assert compilation_time < 120  # Max 2 minutes
            assert memory_used < 500       # Max 500MB additional memory
            
            # Verify substantial output
            content = output_file.read_text()
            assert len(content) > 50000  # Very substantial generated code

    @pytest.mark.performance
    def test_memory_constrained_compilation(self):
        """Test compilation under severe memory constraints."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create moderate-size configuration
            traffic_file, prefectures_file, pattern_count = self.create_large_configuration(
                temp_path, 2000
            )
            output_file = temp_path / 'memory_constrained.py'
            
            # Very constrained memory settings
            config = CompilationConfig(
                max_memory_mb=100,  # Very low memory limit
                chunk_size=128      # Very small chunks
            )
            
            # Monitor memory
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            compiler = ConfigCompiler(config)
            result = compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = peak_memory - initial_memory
            
            # Should succeed despite constraints
            assert output_file.exists()
            assert len(result) > 0
            
            # Memory usage should be controlled
            assert memory_used < 200  # Reasonable memory usage
            
            # Verify output functionality
            content = output_file.read_text()
            namespace = {}
            exec(compile(content, str(output_file), 'exec'), namespace)
            
            # Basic functionality should work
            get_service_time = namespace['get_service_time']
            assert callable(get_service_time)

    @pytest.mark.performance
    def test_streaming_processor_performance(self):
        """Test StreamingPatternProcessor performance."""
        # Create large pattern set for streaming
        large_patterns = {}
        for i in range(10000):
            service_type = ['edge', 'service-hub', 'monitor'][i % 3]
            large_patterns[f'{service_type}.pattern_{i}.*'] = 0.1 + (i * 0.0001)
        
        # Test streaming processing
        expander = EnhancedPatternExpander()
        processor = StreamingPatternProcessor(expander, max_memory_mb=150)
        
        # Monitor performance
        start_time = time.time()
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process in chunks
        results = []
        for chunk_result in processor.process_large_patterns(large_patterns):
            results.append(chunk_result)
        
        end_time = time.time()
        processing_time = end_time - start_time
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = peak_memory - initial_memory
        
        # Performance requirements
        assert processing_time < 60   # Max 1 minute
        assert memory_used < 200      # Max 200MB additional memory
        assert len(results) > 0       # Should produce results
        
        # Verify results quality
        total_processed = sum(len(chunk) for chunk in results)
        assert total_processed >= len(large_patterns)  # At least input size

    @pytest.mark.performance
    def test_json_output_performance(self):
        """Test JSON output performance with large datasets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create large configuration
            traffic_file, prefectures_file, _ = self.create_large_configuration(
                temp_path, 3000
            )
            output_file = temp_path / 'large_output.json'
            
            # Time JSON compilation
            start_time = time.time()
            
            config = CompilationConfig(output_format='json')
            compiler = ConfigCompiler(config)
            result = compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            end_time = time.time()
            compilation_time = end_time - start_time
            
            # Verify performance
            assert output_file.exists()
            assert compilation_time < 45  # Max 45 seconds for JSON
            
            # Verify JSON structure and size
            with open(output_file) as f:
                data = json.load(f)
            
            assert 'component_mapping' in data
            assert len(data['component_mapping']) > 1000  # Should have many entries
            
            # File should be reasonably sized but not excessive
            file_size_mb = output_file.stat().st_size / 1024 / 1024
            assert file_size_mb < 100  # Max 100MB JSON file

    @pytest.mark.performance
    def test_concurrent_compilation_performance(self):
        """Test performance with concurrent compilations."""
        import concurrent.futures
        import threading
        
        def compile_configuration(config_id: int):
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create unique configuration
                traffic_data = {
                    'service_times': {
                        f'service_{config_id}.*.endpoint': 0.1,
                        f'edge_{config_id}.*.gateway': 0.03,
                        f'global_{config_id}.auth': 0.01
                    }
                }
                
                traffic_file = temp_path / f'traffic_{config_id}.yaml'
                with open(traffic_file, 'w') as f:
                    yaml.dump(traffic_data, f)
                
                output_file = temp_path / f'output_{config_id}.py'
                
                # Compile
                compiler = ConfigCompiler(CompilationConfig())
                start_time = time.time()
                result = compiler.compile_traffic_config(
                    traffic_file, None, output_file
                )
                end_time = time.time()
                
                return {
                    'config_id': config_id,
                    'success': output_file.exists(),
                    'compilation_time': end_time - start_time,
                    'output_size': len(result)
                }
        
        # Test concurrent execution
        num_workers = 3
        num_tasks = 10
        
        overall_start = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(compile_configuration, i) for i in range(num_tasks)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        overall_end = time.time()
        total_time = overall_end - overall_start
        
        # Verify all succeeded
        assert len(results) == num_tasks
        assert all(r['success'] for r in results)
        
        # Concurrent execution should be faster than sequential
        sequential_time_estimate = sum(r['compilation_time'] for r in results)
        efficiency = sequential_time_estimate / total_time
        
        # Should have some parallelization benefit
        assert efficiency > 1.0  # At least some improvement
        assert total_time < sequential_time_estimate  # Faster than sequential

    @pytest.mark.performance
    def test_pattern_expansion_scaling(self):
        """Test how pattern expansion scales with different input sizes."""
        expansion_results = []
        
        # Test different pattern counts
        pattern_counts = [100, 500, 1000, 2000]
        
        for pattern_count in pattern_counts:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                traffic_file, prefectures_file, actual_count = self.create_large_configuration(
                    temp_path, pattern_count
                )
                
                # Time pattern expansion only
                compiler = ConfigCompiler(CompilationConfig())
                
                start_time = time.time()
                mapping = compiler._compile_patterns_to_mapping(traffic_file, prefectures_file)
                end_time = time.time()
                
                expansion_time = end_time - start_time
                output_size = len(mapping['component_mapping'])
                
                expansion_results.append({
                    'input_patterns': actual_count,
                    'output_services': output_size,
                    'expansion_time': expansion_time,
                    'expansion_ratio': output_size / actual_count if actual_count > 0 else 0
                })
        
        # Verify scaling characteristics
        assert len(expansion_results) == len(pattern_counts)
        
        # All should complete within reasonable time
        for result in expansion_results:
            assert result['expansion_time'] < 30  # Max 30 seconds each
            assert result['output_services'] > 0  # Should produce output
        
        # Expansion should be consistent
        expansion_ratios = [r['expansion_ratio'] for r in expansion_results]
        assert all(ratio > 1.0 for ratio in expansion_ratios)  # Should expand patterns


class TestMemoryBoundedProcessing:
    """Test processing under various memory constraints."""
    
    @pytest.mark.performance
    def test_extremely_low_memory_processing(self):
        """Test processing with extremely low memory limits."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create moderate configuration
            traffic_data = {
                'service_times': {f'service_{i}.*.endpoint': 0.1 for i in range(1000)}
            }
            
            traffic_file = temp_path / 'traffic.yaml'
            with open(traffic_file, 'w') as f:
                yaml.dump(traffic_data, f)
            
            output_file = temp_path / 'low_memory_output.py'
            
            # Extremely constrained settings
            config = CompilationConfig(
                max_memory_mb=50,   # Very low limit
                chunk_size=64       # Very small chunks
            )
            
            compiler = ConfigCompiler(config)
            
            # Should complete without crashing
            result = compiler.compile_traffic_config(traffic_file, None, output_file)
            
            assert output_file.exists()
            assert len(result) > 0

    @pytest.mark.performance
    def test_memory_cleanup_effectiveness(self):
        """Test that memory cleanup is effective during processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create configuration that would use significant memory
            large_traffic_data = {
                'service_times': {f'service_{i}.pattern_{j}.*': 0.1 + (i*j*0.0001) 
                                 for i in range(200) for j in range(10)}
            }
            
            traffic_file = temp_path / 'large_traffic.yaml'
            with open(traffic_file, 'w') as f:
                yaml.dump(large_traffic_data, f)
            
            output_file = temp_path / 'cleanup_test.py'
            
            # Monitor memory throughout processing
            process = psutil.Process(os.getpid())
            memory_samples = []
            
            def sample_memory():
                while not hasattr(sample_memory, 'stop'):
                    memory_samples.append(process.memory_info().rss / 1024 / 1024)
                    time.sleep(0.1)
            
            # Start memory monitoring
            import threading
            monitor_thread = threading.Thread(target=sample_memory)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            try:
                config = CompilationConfig(max_memory_mb=200)
                compiler = ConfigCompiler(config)
                result = compiler.compile_traffic_config(traffic_file, None, output_file)
            finally:
                sample_memory.stop = True
                monitor_thread.join(timeout=1)
            
            # Analyze memory usage pattern
            if len(memory_samples) > 10:
                max_memory = max(memory_samples)
                min_memory = min(memory_samples)
                memory_variance = max_memory - min_memory
                
                # Memory should be managed (not continuously growing)
                # Allow reasonable variance but not excessive growth
                assert memory_variance < 400  # Max 400MB variance

    @pytest.mark.performance
    def test_cache_efficiency_performance(self):
        """Test cache efficiency with repetitive patterns."""
        # Create patterns with high repetition for cache effectiveness
        repetitive_patterns = {}
        
        # Same base patterns with slight variations
        base_patterns = ['edge.*.gateway', 'service.*.api', 'monitor.*.critical']
        
        for i in range(1000):
            pattern = base_patterns[i % len(base_patterns)]
            # Slight variation to create cache hits and misses
            if i % 10 == 0:
                pattern = f'variant_{i//10}.{pattern}'
            repetitive_patterns[pattern] = 0.1 + (i * 0.0001)
        
        # Test with caching enabled (default)
        expander_cached = EnhancedPatternExpander()
        
        start_time = time.time()
        results_cached = list(expander_cached.expand_pattern_stream(repetitive_patterns))
        cached_time = time.time() - start_time
        
        # Test cache statistics
        cache_stats = expander_cached._expansion_cache.get_stats()
        cache_hit_rate = cache_stats.get('hit_rate', 0) if cache_stats else 0
        
        # Verify performance benefits
        assert cached_time < 30  # Should complete quickly with caching
        assert len(results_cached) > 0
        
        # With repetitive patterns, should have reasonable cache performance
        # (Exact hit rate depends on pattern structure, so we just verify it's working)
        cache_size = len(expander_cached._expansion_cache._cache)
        assert cache_size > 0  # Cache should be populated