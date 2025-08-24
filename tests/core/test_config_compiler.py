"""
Comprehensive tests for ConfigCompiler and related components.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import yaml

from strataregula.core.config_compiler import (
    ConfigCompiler, CompilationConfig, ProvenanceInfo, TemplateEngine
)
from strataregula.core.pattern_expander import EnhancedPatternExpander, RegionHierarchy, ExpansionRule


class TestConfigCompiler:
    """Test ConfigCompiler core functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = CompilationConfig()
        self.compiler = ConfigCompiler(self.config)
        
    def create_test_files(self, temp_dir: Path):
        """Create test configuration files."""
        # Traffic configuration
        traffic_data = {
            'service_times': {
                'edge.*.gateway': 0.03,
                'edge.*.api': 0.05,
                'service-hub.*': 0.08,
                'global.auth': 0.01,
                'monitor.*.*.critical': 0.25
            }
        }
        
        # Prefecture configuration
        prefectures_data = {
            'prefectures': {
                'tokyo': 'kanto',
                'osaka': 'kansai',
                'nagoya': 'chubu'
            },
            'regions': ['kanto', 'kansai', 'chubu'],
            'services': ['edge', 'service-hub', 'monitor'],
            'roles': ['gateway', 'api', 'web'],
            'pattern_rules': {
                'edge.*.*': {
                    'data_source': 'prefectures',
                    'template': 'edge.{prefecture}.{role}',
                    'priority': 100
                },
                'service-hub.*': {
                    'data_source': 'regions',
                    'template': 'service-hub.{region}',
                    'priority': 50
                }
            }
        }
        
        traffic_file = temp_dir / 'traffic.yaml'
        prefectures_file = temp_dir / 'prefectures.yaml'
        
        with open(traffic_file, 'w') as f:
            yaml.dump(traffic_data, f)
        with open(prefectures_file, 'w') as f:
            yaml.dump(prefectures_data, f)
            
        return traffic_file, prefectures_file

    def test_compiler_initialization(self):
        """Test ConfigCompiler initialization."""
        assert self.compiler.config == self.config
        assert isinstance(self.compiler.expander, EnhancedPatternExpander)
        assert isinstance(self.compiler.template_engine, TemplateEngine)

    def test_compiler_custom_config(self):
        """Test ConfigCompiler with custom configuration."""
        custom_config = CompilationConfig(
            output_format='json',
            chunk_size=512,
            max_memory_mb=100,
            include_metadata=False
        )
        compiler = ConfigCompiler(custom_config)
        
        assert compiler.config.output_format == 'json'
        assert compiler.config.chunk_size == 512
        assert compiler.config.max_memory_mb == 100
        assert compiler.config.include_metadata is False

    def test_compile_traffic_config_basic(self):
        """Test basic traffic configuration compilation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_test_files(temp_path)
            output_file = temp_path / 'output.py'
            
            result = self.compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            assert isinstance(result, str)
            assert len(result) > 0
            assert output_file.exists()
            
            # Verify content
            content = output_file.read_text()
            assert 'COMPONENT_MAPPING' in content
            assert 'def get_service_time' in content
            assert 'from typing import Dict, Any, List' in content

    def test_compile_traffic_config_json_format(self):
        """Test compilation with JSON output format."""
        config = CompilationConfig(output_format='json')
        compiler = ConfigCompiler(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_test_files(temp_path)
            output_file = temp_path / 'output.json'
            
            result = compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            assert output_file.exists()
            
            # Verify JSON structure
            with open(output_file) as f:
                data = json.load(f)
            assert 'component_mapping' in data
            assert 'metadata' in data
            assert 'generated_at' in data

    def test_compile_traffic_config_yaml_format(self):
        """Test compilation with YAML output format."""
        config = CompilationConfig(output_format='yaml')
        compiler = ConfigCompiler(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_test_files(temp_path)
            output_file = temp_path / 'output.yaml'
            
            result = compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            assert output_file.exists()
            
            # Verify YAML structure
            with open(output_file) as f:
                data = yaml.safe_load(f)
            assert 'component_mapping' in data
            assert 'metadata' in data

    def test_compile_without_prefectures(self):
        """Test compilation with traffic file only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, _ = self.create_test_files(temp_path)
            output_file = temp_path / 'output.py'
            
            result = self.compiler.compile_traffic_config(
                traffic_file, None, output_file
            )
            
            assert output_file.exists()
            content = output_file.read_text()
            assert 'COMPONENT_MAPPING' in content

    def test_compile_large_batch_patterns(self):
        """Test compilation of large pattern sets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create large traffic configuration
            large_traffic = {'service_times': {}}
            for i in range(100):
                large_traffic['service_times'][f'service_{i}.*.endpoint'] = 0.1 + (i * 0.001)
            
            traffic_file = temp_path / 'large_traffic.yaml'
            with open(traffic_file, 'w') as f:
                yaml.dump(large_traffic, f)
            
            output_file = temp_path / 'large_output.py'
            
            result = self.compiler.compile_traffic_config(
                traffic_file, None, output_file
            )
            
            assert output_file.exists()
            content = output_file.read_text()
            assert 'COMPONENT_MAPPING' in content
            # Should handle large datasets
            assert len(content) > 1000

    def test_pattern_expansion_accuracy(self):
        """Test accuracy of pattern expansion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_test_files(temp_path)
            output_file = temp_path / 'test_expansion.py'
            
            # Compile and check the internal mapping
            self.compiler.compile_traffic_config(traffic_file, prefectures_file, output_file)
            
            # Execute the generated code to test expansion accuracy
            content = output_file.read_text()
            namespace = {}
            exec(compile(content, str(output_file), 'exec'), namespace)
            
            component_mapping = namespace.get('COMPONENT_MAPPING', {})
            
            # Verify expanded patterns
            
            # Should expand edge.*.gateway to all prefectures
            edge_gateways = [k for k in component_mapping.keys() if 'edge.' in k and '.gateway' in k]
            assert len(edge_gateways) >= 3  # At least our test prefectures
            assert 'edge.tokyo.gateway' in component_mapping
            assert 'edge.osaka.gateway' in component_mapping
            
            # Should expand service-hub.* to regions
            service_hubs = [k for k in component_mapping.keys() if 'service-hub.' in k]
            assert len(service_hubs) >= 3  # At least our test regions
            assert 'service-hub.kanto' in component_mapping
            
            # Values should be preserved
            if 'edge.tokyo.gateway' in component_mapping:
                assert component_mapping['edge.tokyo.gateway'] == 0.03

    def test_provenance_tracking(self):
        """Test provenance information tracking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_test_files(temp_path)
            output_file = temp_path / 'output.py'
            
            result = self.compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            content = output_file.read_text()
            
            # Should contain provenance information
            assert str(traffic_file.name) in content
            assert str(prefectures_file.name) in content
            assert 'Generated at:' in content
            assert 'Compilation fingerprint:' in content
            
            # Should contain performance stats in metadata
            assert 'METADATA' in content
            # Check for performance_stats in the generated content structure

    def test_memory_efficient_processing(self):
        """Test memory-efficient processing configuration."""
        config = CompilationConfig(
            max_memory_mb=50,
            chunk_size=256
        )
        compiler = ConfigCompiler(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_test_files(temp_path)
            output_file = temp_path / 'output.py'
            
            result = compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            assert output_file.exists()
            # Should complete successfully with memory constraints

    def test_error_handling_invalid_yaml(self):
        """Test error handling with invalid YAML."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create invalid YAML
            invalid_file = temp_path / 'invalid.yaml'
            invalid_file.write_text("invalid: yaml: content: [")
            
            with pytest.raises(Exception):
                self.compiler.compile_traffic_config(invalid_file, None, None)

    def test_error_handling_missing_file(self):
        """Test error handling with missing files."""
        nonexistent_file = Path('/nonexistent/file.yaml')
        
        try:
            result = self.compiler.compile_traffic_config(nonexistent_file, None, None)
            # If no exception is raised, the method should return error indication
            assert result is None or len(result) == 0
        except Exception as e:
            # Exception is expected - verify it's informative
            assert len(str(e)) > 0

    def test_template_generation_accuracy(self):
        """Test template generation produces correct code."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_test_files(temp_path)
            output_file = temp_path / 'output.py'
            
            result = self.compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            content = output_file.read_text()
            
            # Verify Python syntax by compiling
            try:
                compile(content, str(output_file), 'exec')
            except SyntaxError as e:
                pytest.fail(f"Generated Python code has syntax errors: {e}")
            
            # Verify required functions are present
            assert 'def get_service_time(' in content
            assert 'def get_service_info(' in content
            assert 'def list_all_services(' in content
            assert 'def get_services_by_pattern(' in content


class TestCompilationConfig:
    """Test CompilationConfig dataclass."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = CompilationConfig()
        
        assert config.output_format == 'python'
        assert config.chunk_size == 1024
        assert config.max_memory_mb == 200
        assert config.include_metadata is True
        assert config.include_provenance is True
        assert config.optimize_lookups is True

    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = CompilationConfig(
            output_format='json',
            chunk_size=512,
            max_memory_mb=100,
            include_metadata=False,
            include_provenance=False,
            optimize_lookups=False
        )
        
        assert config.output_format == 'json'
        assert config.chunk_size == 512
        assert config.max_memory_mb == 100
        assert config.include_metadata is False
        assert config.include_provenance is False
        assert config.optimize_lookups is False

    def test_configuration_validation(self):
        """Test configuration validation."""
        # Valid configurations
        config1 = CompilationConfig(output_format='python')
        config2 = CompilationConfig(output_format='json')
        config3 = CompilationConfig(output_format='yaml')
        
        # These should not raise exceptions
        assert config1.output_format == 'python'
        assert config2.output_format == 'json'
        assert config3.output_format == 'yaml'


class TestProvenanceInfo:
    """Test ProvenanceInfo dataclass."""
    
    def test_provenance_creation(self):
        """Test creating provenance information."""
        provenance = ProvenanceInfo(
            timestamp='2025-08-24T12:00:00',
            version='0.1.1',
            input_files=['traffic.yaml', 'prefectures.yaml'],
            execution_fingerprint='abc123',
            performance_stats={'compilation_time': 0.5}
        )
        
        assert provenance.timestamp == '2025-08-24T12:00:00'
        assert provenance.version == '0.1.1'
        assert len(provenance.input_files) == 2
        assert provenance.execution_fingerprint == 'abc123'
        assert provenance.performance_stats['compilation_time'] == 0.5


class TestTemplateEngine:
    """Test TemplateEngine functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.template_engine = TemplateEngine()
        
    def test_template_engine_python_format(self):
        """Test Python template rendering."""
        context = {
            'timestamp': '2025-08-24T12:00:00',
            'input_files': 'test.yaml',
            'fingerprint': 'abc123',
            'direct_mapping_code': '{}',
            'component_mapping_code': '{"test": 0.1}',
            'metadata_code': '{"version": "0.1.1"}',
            'hierarchical_functions': 'def test(): pass'
        }
        
        result = self.template_engine.render('python', context)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert 'def get_service_time' in result
        assert 'COMPONENT_MAPPING' in result
        assert 'from typing import Dict, Any, List' in result
        
        # Verify it's valid Python
        try:
            compile(result, '<string>', 'exec')
        except SyntaxError as e:
            pytest.fail(f"Generated Python template has syntax errors: {e}")

    def test_template_engine_json_format(self):
        """Test JSON template rendering."""
        context = {
            'timestamp': '2025-08-24T12:00:00',
            'fingerprint': 'abc123',
            'direct_mapping': '{}',
            'component_mapping': '{"test": 0.1}',
            'metadata': '{"version": "0.1.1"}'
        }
        
        result = self.template_engine.render('json', context)
        
        assert isinstance(result, str)
        # Should be valid JSON structure
        assert '"direct_mapping":' in result
        assert '"component_mapping":' in result
        assert '"metadata":' in result

    def test_template_engine_yaml_format(self):
        """Test YAML template rendering."""
        context = {
            'timestamp': '2025-08-24T12:00:00',
            'fingerprint': 'abc123',
            'direct_mapping_yaml': 'direct_mapping: {}',
            'component_mapping_yaml': 'component_mapping:\n  test: 0.1',
            'metadata_yaml': 'metadata:\n  version: 0.1.1'
        }
        
        result = self.template_engine.render('yaml', context)
        
        assert isinstance(result, str)
        assert 'direct_mapping:' in result
        assert 'component_mapping:' in result
        assert 'metadata:' in result

    def test_template_engine_invalid_format(self):
        """Test error handling with invalid format."""
        context = {}
        
        with pytest.raises(ValueError):
            self.template_engine.render('invalid_format', context)

    def test_template_context_validation(self):
        """Test template rendering with missing context variables."""
        incomplete_context = {
            'timestamp': '2025-08-24T12:00:00'
            # Missing other required variables
        }
        
        # Should raise KeyError for missing template variables
        with pytest.raises(KeyError):
            self.template_engine.render('python', incomplete_context)


# Performance and stress tests
class TestConfigCompilerPerformance:
    """Performance tests for ConfigCompiler."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = CompilationConfig()
        self.compiler = ConfigCompiler(self.config)
    
    @pytest.mark.performance
    def test_large_pattern_set_compilation(self):
        """Test compilation performance with large pattern sets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create large configuration
            large_traffic = {'service_times': {}}
            
            # Generate 1000 test patterns
            for i in range(1000):
                service_type = ['edge', 'service-hub', 'corebrain'][i % 3]
                large_traffic['service_times'][f'{service_type}.pattern_{i}.*'] = 0.1 + (i * 0.0001)
            
            traffic_file = temp_path / 'large_traffic.yaml'
            with open(traffic_file, 'w') as f:
                yaml.dump(large_traffic, f)
            
            output_file = temp_path / 'large_output.py'
            
            # Measure compilation time
            import time
            start_time = time.time()
            
            result = self.compiler.compile_traffic_config(
                traffic_file, None, output_file
            )
            
            end_time = time.time()
            compilation_time = end_time - start_time
            
            assert output_file.exists()
            assert compilation_time < 60  # Should complete within 1 minute
            
            # Verify output quality
            content = output_file.read_text()
            assert 'COMPONENT_MAPPING' in content
            assert len(content) > 10000  # Should generate substantial code

    @pytest.mark.performance
    def test_memory_usage_monitoring(self):
        """Test memory usage during compilation."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create moderately large configuration
            traffic_data = {'service_times': {}}
            for i in range(500):
                traffic_data['service_times'][f'service_{i}.*.endpoint'] = 0.1
            
            traffic_file = temp_path / 'traffic.yaml'
            with open(traffic_file, 'w') as f:
                yaml.dump(traffic_data, f)
            
            output_file = temp_path / 'output.py'
            
            result = self.compiler.compile_traffic_config(
                traffic_file, None, output_file
            )
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable
            assert memory_increase < 500  # Less than 500MB increase
            assert output_file.exists()

    @pytest.mark.performance
    def test_concurrent_compilation(self):
        """Test multiple concurrent compilations."""
        import concurrent.futures
        import threading
        
        def compile_config(suffix: int):
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                traffic_data = {
                    'service_times': {
                        f'service_{suffix}.*.endpoint': 0.1,
                        f'edge_{suffix}.*.gateway': 0.03
                    }
                }
                
                traffic_file = temp_path / f'traffic_{suffix}.yaml'
                with open(traffic_file, 'w') as f:
                    yaml.dump(traffic_data, f)
                
                output_file = temp_path / f'output_{suffix}.py'
                
                compiler = ConfigCompiler(CompilationConfig())
                result = compiler.compile_traffic_config(
                    traffic_file, None, output_file
                )
                
                return output_file.exists()
        
        # Test concurrent execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(compile_config, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All compilations should succeed
        assert all(results)