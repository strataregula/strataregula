"""
Comprehensive tests for CLI compile command functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
import yaml
from click.testing import CliRunner

from strataregula.cli.compile_command import compile_cmd


class TestCompileCommandCLI:
    """Test compile command CLI interface."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        
    def create_sample_files(self, temp_dir: Path):
        """Create sample configuration files for testing."""
        # Sample traffic config
        traffic_data = {
            'service_times': {
                'edge.*.gateway': 0.03,
                'edge.*.api': 0.05,
                'service-hub.*': 0.08,
                'global.auth': 0.01,
                'global.metrics': 0.005
            }
        }
        
        # Sample prefecture config  
        prefectures_data = {
            'prefectures': {
                'tokyo': 'kanto',
                'osaka': 'kansai', 
                'nagoya': 'chubu'
            },
            'regions': ['kanto', 'kansai', 'chubu'],
            'services': ['edge', 'service-hub', 'gateway', 'api'],
            'roles': ['gateway', 'api', 'web'],
            'pattern_rules': {
                'edge.*.*': {
                    'data_source': 'prefectures',
                    'template': 'edge.{prefecture}.{role}',
                    'description': 'Edge services by prefecture',
                    'priority': 100
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

    def test_compile_help_display(self):
        """Test that --help displays correct information."""
        result = self.runner.invoke(compile_cmd, ['--help'])
        
        assert result.exit_code == 0
        assert 'Compile configuration patterns' in result.output
        assert '--traffic' in result.output
        assert '--prefectures' in result.output
        assert '--out' in result.output
        assert '--format' in result.output

    def test_compile_missing_traffic_file(self):
        """Test error handling when traffic file is missing."""
        result = self.runner.invoke(compile_cmd, [])
        
        assert result.exit_code == 2
        assert 'Missing option' in result.output or 'Error' in result.output

    def test_compile_basic_functionality(self):
        """Test basic compilation with minimal setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_sample_files(temp_path)
            output_file = temp_path / 'output.py'
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(traffic_file),
                '--prefectures', str(prefectures_file),
                '--out', str(output_file)
            ])
            
            assert result.exit_code == 0
            assert output_file.exists()
            assert 'Compilation completed successfully' in result.output or 'successful' in result.output.lower()
            
            # Verify generated Python file contains expected content
            content = output_file.read_text()
            assert 'COMPONENT_MAPPING' in content
            assert 'def get_service_time' in content
            assert 'edge.tokyo.gateway' in content or 'edge' in content

    def test_compile_json_output(self):
        """Test JSON output format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_sample_files(temp_path)
            output_file = temp_path / 'output.json'
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(traffic_file),
                '--prefectures', str(prefectures_file),
                '--format', 'json',
                '--out', str(output_file)
            ])
            
            assert result.exit_code == 0
            assert output_file.exists()
            
            # Verify JSON is valid and contains expected structure
            with open(output_file) as f:
                data = json.load(f)
            assert 'component_mapping' in data
            assert 'metadata' in data
            assert isinstance(data['component_mapping'], dict)

    def test_compile_yaml_output(self):
        """Test YAML output format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_sample_files(temp_path)
            output_file = temp_path / 'output.yaml'
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(traffic_file),
                '--prefectures', str(prefectures_file),
                '--format', 'yaml',
                '--out', str(output_file)
            ])
            
            assert result.exit_code == 0
            assert output_file.exists()
            
            # Verify YAML is valid
            with open(output_file) as f:
                data = yaml.safe_load(f)
            assert 'component_mapping' in data
            assert isinstance(data['component_mapping'], dict)

    def test_compile_plan_mode(self):
        """Test --plan mode that shows analysis without compilation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_sample_files(temp_path)
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(traffic_file),
                '--prefectures', str(prefectures_file),
                '--plan'
            ])
            
            assert result.exit_code == 0
            assert 'Compilation Plan' in result.output
            assert 'Service patterns:' in result.output or 'patterns' in result.output.lower()
            assert 'Processing strategy:' in result.output or 'strategy' in result.output.lower()

    def test_compile_stats_mode(self):
        """Test --stats mode that shows detailed statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_sample_files(temp_path)
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(traffic_file),
                '--prefectures', str(prefectures_file),
                '--stats'
            ])
            
            assert result.exit_code == 0
            assert 'Statistics' in result.output or 'stats' in result.output.lower()

    def test_compile_validate_only_mode(self):
        """Test --validate-only mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_sample_files(temp_path)
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(traffic_file),
                '--prefectures', str(prefectures_file),
                '--validate-only'
            ])
            
            assert result.exit_code == 0

    def test_compile_verbose_output(self):
        """Test verbose mode provides detailed output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_sample_files(temp_path)
            output_file = temp_path / 'output.py'
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(traffic_file),
                '--prefectures', str(prefectures_file),
                '--out', str(output_file),
                '--verbose'
            ])
            
            assert result.exit_code == 0
            # Verbose mode should provide more detailed output
            assert len(result.output) > 100  # Should have substantial output

    def test_compile_memory_limit_configuration(self):
        """Test memory limit configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_sample_files(temp_path)
            output_file = temp_path / 'output.py'
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(traffic_file),
                '--prefectures', str(prefectures_file),
                '--out', str(output_file),
                '--max-memory', '50',
                '--chunk-size', '512'
            ])
            
            assert result.exit_code == 0
            assert output_file.exists()

    def test_compile_invalid_traffic_file(self):
        """Test error handling with invalid traffic file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            invalid_file = temp_path / 'invalid.yaml'
            invalid_file.write_text("invalid: yaml: content: [")
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(invalid_file)
            ])
            
            # Should handle error gracefully
            assert result.exit_code != 0

    def test_compile_nonexistent_file(self):
        """Test error handling with nonexistent files."""
        result = self.runner.invoke(compile_cmd, [
            '--traffic', '/nonexistent/file.yaml'
        ])
        
        assert result.exit_code != 0
        assert 'Error' in result.output or 'error' in result.output.lower()

    def test_compile_output_directory_creation(self):
        """Test that output directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, prefectures_file = self.create_sample_files(temp_path)
            
            # Output to nested directory that doesn't exist
            output_file = temp_path / 'nested' / 'dir' / 'output.py'
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(traffic_file),
                '--prefectures', str(prefectures_file),
                '--out', str(output_file)
            ])
            
            # Should create directory and file
            if result.exit_code == 0:
                assert output_file.exists()

    def test_compile_no_prefectures_file(self):
        """Test compilation with traffic file only (no prefectures)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            traffic_file, _ = self.create_sample_files(temp_path)
            output_file = temp_path / 'output.py'
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(traffic_file),
                '--out', str(output_file)
            ])
            
            # Should work with default hierarchy
            assert result.exit_code == 0
            assert output_file.exists()

    @pytest.mark.performance
    def test_compile_performance_basic(self):
        """Basic performance test for compile command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create larger test data
            traffic_data = {
                'service_times': {}
            }
            
            # Generate test patterns
            for service in ['edge', 'service-hub', 'corebrain']:
                for i in range(10):
                    traffic_data['service_times'][f'{service}.pattern_{i}.*'] = 0.1 + (i * 0.01)
            
            traffic_file = temp_path / 'large_traffic.yaml'
            with open(traffic_file, 'w') as f:
                yaml.dump(traffic_data, f)
            
            output_file = temp_path / 'output.py'
            
            # Time the compilation
            import time
            start_time = time.time()
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(traffic_file),
                '--out', str(output_file)
            ])
            
            end_time = time.time()
            compilation_time = end_time - start_time
            
            assert result.exit_code == 0
            assert output_file.exists()
            # Should complete within reasonable time (adjust as needed)
            assert compilation_time < 30  # 30 seconds max for basic performance


class TestCompileCommandErrorHandling:
    """Test error handling and edge cases."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()

    def test_compile_with_write_protected_output(self):
        """Test handling of write-protected output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a simple traffic file
            traffic_data = {'service_times': {'test.service': 0.1}}
            traffic_file = temp_path / 'traffic.yaml'
            with open(traffic_file, 'w') as f:
                yaml.dump(traffic_data, f)
            
            # Try to write to a directory that doesn't exist or is protected
            protected_output = Path('/root/protected/output.py')  # Unix-style protected path
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(traffic_file),
                '--out', str(protected_output)
            ])
            
            # Should handle the error gracefully
            # On Windows, this might succeed or fail differently
            if result.exit_code != 0:
                assert ('Error' in result.output or 'error' in result.output.lower() or 
                       'failed' in result.output.lower())

    def test_compile_with_malformed_yaml(self):
        """Test handling of malformed YAML files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create malformed YAML
            malformed_file = temp_path / 'malformed.yaml'
            malformed_file.write_text("""
            service_times:
                edge.*.gateway: 0.03
                invalid: yaml: structure: [
                    unclosed: list
            """)
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(malformed_file)
            ])
            
            assert result.exit_code != 0

    def test_compile_empty_configuration(self):
        """Test handling of empty configuration files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create empty YAML file
            empty_file = temp_path / 'empty.yaml'
            empty_file.write_text("")
            
            output_file = temp_path / 'output.py'
            
            result = self.runner.invoke(compile_cmd, [
                '--traffic', str(empty_file),
                '--out', str(output_file)
            ])
            
            # Should handle empty file gracefully
            # May succeed with empty output or fail with appropriate error
            if result.exit_code == 0:
                assert output_file.exists()


# Integration tests that verify CLI works with real example files
class TestCompileCommandIntegration:
    """Integration tests using real example files."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        
    def test_compile_with_example_files(self):
        """Test compilation using actual example files from the project."""
        # Use existing example files if they exist
        project_root = Path(__file__).parent.parent.parent
        traffic_file = project_root / 'examples' / 'sample_traffic.yaml'
        prefectures_file = project_root / 'examples' / 'sample_prefectures.yaml'
        
        if traffic_file.exists() and prefectures_file.exists():
            with tempfile.TemporaryDirectory() as temp_dir:
                output_file = Path(temp_dir) / 'integration_output.py'
                
                result = self.runner.invoke(compile_cmd, [
                    '--traffic', str(traffic_file),
                    '--prefectures', str(prefectures_file),
                    '--out', str(output_file)
                ])
                
                assert result.exit_code == 0
                assert output_file.exists()
                
                # Verify the generated file can be imported as Python
                content = output_file.read_text()
                assert 'def get_service_time' in content
                assert 'COMPONENT_MAPPING' in content
                
                # Basic syntax check by compiling the Python code
                try:
                    compile(content, str(output_file), 'exec')
                except SyntaxError:
                    pytest.fail("Generated Python code has syntax errors")
        else:
            pytest.skip("Example files not found, skipping integration test")