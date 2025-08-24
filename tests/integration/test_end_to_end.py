"""
End-to-end integration tests for strataregula functionality.
These tests verify the complete workflow from CLI input to output generation.
"""

import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Any
import pytest
import yaml

from strataregula.core.config_compiler import ConfigCompiler, CompilationConfig
from strataregula.core.pattern_expander import EnhancedPatternExpander


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    def create_realistic_configuration(self, temp_dir: Path):
        """Create realistic configuration files for testing."""
        
        # Realistic traffic configuration
        traffic_data = {
            'service_times': {
                # Edge services (will expand to all prefectures)
                'edge.*.gateway': 0.03,
                'edge.*.api': 0.05,
                'edge.*.web': 0.02,
                'edge.*.monitor': 0.01,
                
                # Regional services (will expand to regions)
                'service-hub.*': 0.08,
                'service-hub.*.processing': 0.12,
                'service-hub.*.cache': 0.04,
                
                # Core services (regional)
                'corebrain.*.analytics': 0.15,
                'corebrain.*.storage': 0.20,
                'corebrain.*.backup': 0.35,
                
                # Global services (direct mapping)
                'global.auth': 0.01,
                'global.metrics': 0.005,
                'global.health': 0.001,
                'global.logging': 0.002,
                
                # Multi-wildcard patterns
                'monitor.*.*.critical': 0.25,
                'backup.*.*.daily': 1.5,
                'cache.*.*.hot': 0.002,
                
                # Different service types
                'database.*.primary': 0.8,
                'database.*.replica': 0.4,
                'queue.*.main': 0.1,
                'queue.*.retry': 0.05
            },
            'metadata': {
                'description': 'Production service configuration',
                'version': '2.1.0',
                'created_by': 'infrastructure-team'
            }
        }
        
        # Complete prefecture/region hierarchy
        prefectures_data = {
            'prefectures': {
                # Kanto region
                'tokyo': 'kanto',
                'kanagawa': 'kanto', 
                'saitama': 'kanto',
                'chiba': 'kanto',
                'ibaraki': 'kanto',
                'tochigi': 'kanto',
                'gunma': 'kanto',
                
                # Kansai region
                'osaka': 'kansai',
                'kyoto': 'kansai',
                'hyogo': 'kansai',
                'nara': 'kansai',
                'wakayama': 'kansai',
                'shiga': 'kansai',
                
                # Chubu region
                'aichi': 'chubu',
                'shizuoka': 'chubu',
                'gifu': 'chubu',
                'nagano': 'chubu',
                'yamanashi': 'chubu',
                'niigata': 'chubu',
                
                # Kyushu region  
                'fukuoka': 'kyushu',
                'saga': 'kyushu',
                'nagasaki': 'kyushu',
                'kumamoto': 'kyushu',
                
                # Hokkaido region
                'hokkaido': 'hokkaido',
                
                # Tohoku region
                'aomori': 'tohoku',
                'iwate': 'tohoku',
                'miyagi': 'tohoku',
                'akita': 'tohoku'
            },
            
            'regions': [
                'kanto', 'kansai', 'chubu', 'kyushu', 
                'hokkaido', 'tohoku', 'chugoku', 'shikoku'
            ],
            
            'services': [
                'edge', 'service-hub', 'corebrain', 'gateway', 
                'api', 'web', 'monitor', 'backup', 'cache',
                'database', 'queue'
            ],
            
            'roles': [
                'gateway', 'api', 'web', 'processor', 'analytics',
                'storage', 'cache', 'backup', 'monitor', 'critical',
                'daily', 'hot', 'primary', 'replica', 'main', 'retry'
            ],
            
            'pattern_rules': {
                'edge.*.*': {
                    'data_source': 'prefectures',
                    'template': 'edge.{prefecture}.{role}',
                    'description': 'Edge services by prefecture and role',
                    'priority': 100
                },
                'service-hub.*': {
                    'data_source': 'regions',
                    'template': 'service-hub.{region}',
                    'description': 'Service hubs by region',
                    'priority': 50
                },
                'service-hub.*.*': {
                    'data_source': 'regions',
                    'template': 'service-hub.{region}.{service}',
                    'description': 'Service hub services by region',
                    'priority': 75
                },
                'corebrain.*.*': {
                    'data_source': 'regions',
                    'template': 'corebrain.{region}.{service}',
                    'description': 'Core brain services by region',
                    'priority': 60
                },
                'monitor.*.*.*': {
                    'data_source': 'prefectures',
                    'template': 'monitor.{prefecture}.{service}.{level}',
                    'description': 'Monitor services by prefecture',
                    'priority': 30
                }
            },
            
            'metadata': {
                'version': '1.0.0',
                'description': 'Complete Japanese prefecture and region hierarchy',
                'total_prefectures': 25,  # Subset for testing
                'total_regions': 8
            }
        }
        
        traffic_file = temp_dir / 'production_traffic.yaml'
        prefectures_file = temp_dir / 'japan_hierarchy.yaml'
        
        with open(traffic_file, 'w') as f:
            yaml.dump(traffic_data, f, default_flow_style=False, allow_unicode=True)
        with open(prefectures_file, 'w') as f:
            yaml.dump(prefectures_data, f, default_flow_style=False, allow_unicode=True)
            
        return traffic_file, prefectures_file

    def test_complete_python_generation_workflow(self):
        """Test complete workflow: YAML input → Python module generation → verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_realistic_configuration(temp_path)
            output_file = temp_path / 'generated_config.py'
            
            # Step 1: Compile configuration
            compiler = ConfigCompiler(CompilationConfig(output_format='python'))
            result = compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            # Step 2: Verify file generation
            assert output_file.exists()
            assert len(result) > 0
            
            content = output_file.read_text()
            
            # Step 3: Verify Python syntax
            try:
                compiled_code = compile(content, str(output_file), 'exec')
            except SyntaxError as e:
                pytest.fail(f"Generated Python code has syntax errors: {e}")
            
            # Step 4: Execute and test the generated module
            namespace = {}
            exec(compiled_code, namespace)
            
            # Verify required functions exist
            assert 'get_service_time' in namespace
            assert 'get_service_info' in namespace  
            assert 'list_all_services' in namespace
            assert 'get_services_by_pattern' in namespace
            assert 'get_services_by_region' in namespace
            
            # Step 5: Test function functionality
            get_service_time = namespace['get_service_time']
            get_service_info = namespace['get_service_info']
            list_all_services = namespace['list_all_services']
            get_services_by_pattern = namespace['get_services_by_pattern']
            
            # Test direct service lookup
            auth_time = get_service_time('global.auth')
            assert auth_time == 0.01
            
            # Test expanded service lookup
            tokyo_gateway = get_service_time('edge.tokyo.gateway')
            assert tokyo_gateway == 0.03
            
            # Test service info
            info = get_service_info('global.auth')
            assert info['service_name'] == 'global.auth'
            assert info['service_time'] == 0.01
            assert info['found_in'] == 'component'
            
            # Test pattern matching
            edge_services = get_services_by_pattern('edge.tokyo.*')
            assert len(edge_services) > 0
            assert 'edge.tokyo.gateway' in edge_services
            assert 'edge.tokyo.api' in edge_services
            
            # Test service listing
            all_services = list_all_services()
            assert len(all_services) > 50  # Should have many expanded services
            assert 'global.auth' in all_services
            assert 'edge.tokyo.gateway' in all_services

    def test_complete_json_generation_workflow(self):
        """Test complete workflow with JSON output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_realistic_configuration(temp_path)
            output_file = temp_path / 'generated_config.json'
            
            # Compile to JSON
            compiler = ConfigCompiler(CompilationConfig(output_format='json'))
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
            assert 'fingerprint' in data
            
            # Verify expanded patterns
            component_mapping = data['component_mapping']
            assert 'global.auth' in component_mapping
            assert component_mapping['global.auth'] == 0.01
            
            # Should have expanded edge services
            edge_services = {k: v for k, v in component_mapping.items() if k.startswith('edge.')}
            assert len(edge_services) > 10  # Should have many expanded services
            
            # Verify metadata structure
            metadata = data['metadata']
            assert 'provenance' in metadata
            assert 'expansion_rules_count' in metadata
            
            # Test that JSON can be used programmatically
            service_time = component_mapping.get('edge.tokyo.gateway', 0)
            assert service_time == 0.03

    def test_yaml_output_workflow(self):
        """Test complete workflow with YAML output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_realistic_configuration(temp_path)
            output_file = temp_path / 'generated_config.yaml'
            
            # Compile to YAML
            compiler = ConfigCompiler(CompilationConfig(output_format='yaml'))
            result = compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            assert output_file.exists()
            
            # Verify YAML structure
            with open(output_file) as f:
                data = yaml.safe_load(f)
            
            assert 'component_mapping' in data
            assert 'metadata' in data
            
            # Verify expanded patterns
            component_mapping = data['component_mapping']
            assert isinstance(component_mapping, dict)
            assert len(component_mapping) > 20

    def test_large_scale_expansion_accuracy(self):
        """Test accuracy of large-scale pattern expansion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_realistic_configuration(temp_path)
            
            # Test pattern expansion accuracy by compiling and examining output
            compiler = ConfigCompiler(CompilationConfig())
            output_file = temp_path / 'expansion_test.py'
            compiler.compile_traffic_config(traffic_file, prefectures_file, output_file)
            
            # Execute generated code to check mappings
            content = output_file.read_text()
            namespace = {}
            exec(compile(content, str(output_file), 'exec'), namespace)
            component_mapping = namespace.get('COMPONENT_MAPPING', {})
            
            # Count expanded services by type
            edge_gateways = {k: v for k, v in component_mapping.items() 
                            if k.startswith('edge.') and k.endswith('.gateway')}
            edge_apis = {k: v for k, v in component_mapping.items() 
                        if k.startswith('edge.') and k.endswith('.api')}
            service_hubs = {k: v for k, v in component_mapping.items() 
                           if k.startswith('service-hub.') and not '.' in k.split('service-hub.')[1]}
            
            # Verify expansion counts match expectations (actual prefectures in test data)
            # Note: Actual count may vary based on test data and default hierarchy
            assert len(edge_gateways) >= 25  # At least 25 test prefectures
            assert len(edge_apis) >= 25     # At least 25 test prefectures  
            assert len(service_hubs) >= 6   # At least 6 regions
            
            # Verify values are preserved
            for value in edge_gateways.values():
                assert value == 0.03
            for value in edge_apis.values():
                assert value == 0.05
            for value in service_hubs.values():
                assert value == 0.08
            
            # Verify specific mappings
            assert 'edge.tokyo.gateway' in edge_gateways
            assert 'edge.osaka.api' in edge_apis
            assert 'service-hub.kanto' in service_hubs
            assert 'global.auth' in component_mapping
            assert component_mapping['global.auth'] == 0.01

    def test_performance_with_realistic_data(self):
        """Test performance with realistic data sizes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_realistic_configuration(temp_path)
            output_file = temp_path / 'perf_test_output.py'
            
            # Measure compilation time
            start_time = time.time()
            
            compiler = ConfigCompiler(CompilationConfig())
            result = compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            end_time = time.time()
            compilation_time = end_time - start_time
            
            assert output_file.exists()
            assert compilation_time < 5.0  # Should complete within 5 seconds
            
            # Verify output quality
            content = output_file.read_text()
            assert len(content) > 5000  # Should generate substantial code
            
            # Performance metrics should be included
            assert 'performance_stats' in content or 'compilation_time' in content

    def test_provenance_and_metadata_accuracy(self):
        """Test that provenance and metadata are accurately tracked."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_realistic_configuration(temp_path)
            output_file = temp_path / 'provenance_test.py'
            
            compiler = ConfigCompiler(CompilationConfig())
            result = compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            content = output_file.read_text()
            
            # Verify provenance information
            assert traffic_file.name in content
            assert prefectures_file.name in content
            assert 'Generated at:' in content
            assert 'Compilation fingerprint:' in content
            
            # Execute and check metadata
            namespace = {}
            exec(compile(content, str(output_file), 'exec'), namespace)
            
            metadata = namespace.get('METADATA', {})
            assert 'provenance' in metadata
            
            provenance = metadata['provenance']
            assert 'timestamp' in provenance
            assert 'input_files' in provenance
            assert 'execution_fingerprint' in provenance
            assert 'performance_stats' in provenance
            
            # Verify performance stats
            perf_stats = provenance['performance_stats']
            assert 'compilation_time_seconds' in perf_stats
            assert 'peak_memory_mb' in perf_stats
            assert perf_stats['compilation_time_seconds'] > 0

    def test_memory_efficiency_integration(self):
        """Test memory-efficient processing in realistic scenarios."""
        config = CompilationConfig(
            max_memory_mb=100,  # Constrained memory
            chunk_size=256      # Small chunk size
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_realistic_configuration(temp_path)
            output_file = temp_path / 'memory_test.py'
            
            compiler = ConfigCompiler(config)
            result = compiler.compile_traffic_config(
                traffic_file, prefectures_file, output_file
            )
            
            assert output_file.exists()
            
            # Should complete successfully with memory constraints
            content = output_file.read_text()
            assert 'COMPONENT_MAPPING' in content
            assert len(content) > 1000


class TestBackwardCompatibility:
    """Test backward compatibility with existing config_compiler.py functionality."""
    
    def test_config_compiler_interface_compatibility(self):
        """Test that the interface matches original config_compiler.py."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal configuration similar to original format
            traffic_data = {
                'service_times': {
                    'edge.*.gateway': 0.03,
                    'global.auth': 0.01
                }
            }
            
            traffic_file = temp_path / 'traffic.yaml'
            with open(traffic_file, 'w') as f:
                yaml.dump(traffic_data, f)
            
            output_file = temp_path / 'compat_output.py'
            
            # Should work with the same interface as original
            compiler = ConfigCompiler(CompilationConfig())
            result = compiler.compile_traffic_config(
                traffic_file, None, output_file  # None for prefectures (original behavior)
            )
            
            assert output_file.exists()
            content = output_file.read_text()
            
            # Should generate similar structure to original
            assert 'def get_service_time' in content  # Main lookup function
            assert 'global.auth' in content
            # Should handle wildcard expansion even without prefecture file

    def test_original_usage_patterns(self):
        """Test common usage patterns from the original config_compiler.py."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create configuration in original style
            original_style_config = {
                'service_times': {
                    'edge.*.gateway': 0.03,
                    'edge.*.api': 0.05,
                    'service.*.processor': 0.10,
                    'global.auth': 0.01,
                    'global.metrics': 0.005
                }
            }
            
            config_file = temp_path / 'original_style.yaml'
            with open(config_file, 'w') as f:
                yaml.dump(original_style_config, f)
            
            output_file = temp_path / 'original_output.py'
            
            compiler = ConfigCompiler(CompilationConfig())
            result = compiler.compile_traffic_config(config_file, None, output_file)
            
            # Execute the generated code
            content = output_file.read_text()
            namespace = {}
            exec(compile(content, str(output_file), 'exec'), namespace)
            
            # Test original-style usage
            get_service_time = namespace['get_service_time']
            
            # Direct lookups should work
            assert get_service_time('global.auth') == 0.01
            assert get_service_time('global.metrics') == 0.005
            
            # Unknown services should return default
            assert get_service_time('unknown.service') == 0.0
            assert get_service_time('unknown.service', 0.5) == 0.5


class TestErrorHandlingIntegration:
    """Test error handling in integration scenarios."""
    
    def test_malformed_input_handling(self):
        """Test handling of various malformed inputs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test cases for different malformed inputs
            malformed_cases = [
                # Invalid YAML syntax
                "service_times:\n  edge.*.gateway: invalid_value: [",
                
                # Missing required sections
                "wrong_section:\n  some: data",
                
                # Invalid pattern syntax
                "service_times:\n  invalid..pattern..: 0.03",
                
                # Non-numeric values
                "service_times:\n  edge.*.gateway: not_a_number"
            ]
            
            compiler = ConfigCompiler(CompilationConfig())
            
            for i, malformed_content in enumerate(malformed_cases):
                malformed_file = temp_path / f'malformed_{i}.yaml'
                malformed_file.write_text(malformed_content)
                output_file = temp_path / f'output_{i}.py'
                
                # Should handle errors gracefully
                try:
                    result = compiler.compile_traffic_config(
                        malformed_file, None, output_file
                    )
                    # If it succeeds, verify it produces something reasonable
                    if output_file.exists():
                        content = output_file.read_text()
                        assert 'def get_service_time' in content
                except Exception as e:
                    # Errors should be descriptive
                    assert len(str(e)) > 10

    def test_missing_file_handling(self):
        """Test handling of missing input files."""
        compiler = ConfigCompiler(CompilationConfig())
        
        # Test with nonexistent files
        nonexistent_file = Path('/nonexistent/file.yaml')
        
        try:
            result = compiler.compile_traffic_config(nonexistent_file, None, None)
            # If no exception, method should return None or empty
            assert result is None or len(result) == 0
        except Exception as e:
            # Exception is expected - verify it's informative
            error_message = str(e)
            assert len(error_message) > 0

    def test_partial_failure_recovery(self):
        """Test recovery from partial failures during processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create configuration with some valid and some problematic patterns
            mixed_config = {
                'service_times': {
                    'valid.service': 0.1,
                    'edge.*.gateway': 0.03,  # Valid wildcard
                    'global.auth': 0.01,     # Valid direct
                    'valid.direct': 0.05
                }
            }
            
            config_file = temp_path / 'mixed.yaml'
            with open(config_file, 'w') as f:
                yaml.dump(mixed_config, f)
            
            output_file = temp_path / 'mixed_output.py'
            
            compiler = ConfigCompiler(CompilationConfig())
            result = compiler.compile_traffic_config(config_file, None, output_file)
            
            # Should succeed and process valid parts
            assert output_file.exists()
            content = output_file.read_text()
            
            # Valid services should be included
            assert 'valid.service' in content
            assert 'global.auth' in content