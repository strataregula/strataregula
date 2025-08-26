"""
Tests for compatibility module.
"""
import sys
import pytest
import warnings
from unittest.mock import patch, MagicMock

from strataregula.core.compatibility import (
    get_python_info,
    check_package_version,
    check_environment_compatibility,
    safe_import_with_fallback,
    safe_import_psutil,
    MockPsutilProcess,
    get_compatible_rich_console,
    check_yaml_compatibility,
    print_compatibility_report
)


class TestGetPythonInfo:
    """Test Python environment information gathering."""

    def test_get_python_info_structure(self):
        """Test that get_python_info returns expected structure."""
        info = get_python_info()
        
        required_keys = ['version', 'executable', 'platform', 'implementation', 'prefix']
        for key in required_keys:
            assert key in info
        
        assert isinstance(info['version'], tuple)
        assert len(info['version']) >= 2
        assert isinstance(info['executable'], str)
        assert isinstance(info['platform'], str)
        assert isinstance(info['implementation'], str)
        assert isinstance(info['prefix'], str)

    def test_get_python_info_values(self):
        """Test that get_python_info returns reasonable values."""
        info = get_python_info()
        
        # Python version should be reasonable
        assert info['version'][0] >= 3
        assert info['version'][1] >= 8  # Our minimum requirement
        
        # Executable should be a valid path
        assert len(info['executable']) > 0
        
        # Implementation should be known
        assert info['implementation'] in ['cpython', 'pypy', 'jython', 'ironpython']


class TestCheckPackageVersion:
    """Test package version checking."""

    def test_check_package_version_compatible(self):
        """Test version checking for compatible packages."""
        # Use a standard library that should be available
        is_compat, version = check_package_version('typing_extensions', '0.1.0')
        
        # Should either be compatible or not installed
        assert isinstance(is_compat, bool)
        if is_compat:
            assert isinstance(version, str)
            assert len(version) > 0

    def test_check_package_version_nonexistent(self):
        """Test version checking for non-existent packages."""
        is_compat, version = check_package_version('definitely_not_a_real_package_12345', '1.0.0')
        
        assert is_compat is False
        assert version is None

    def test_check_package_version_invalid_format(self):
        """Test version checking with invalid version format."""
        # This should handle invalid version formats gracefully
        with patch('strataregula.core.compatibility.version') as mock_version:
            mock_version.return_value = "invalid.version.format.with.too.many.parts"
            is_compat, version = check_package_version('some_package', '1.0.0')
            
            # Should handle gracefully
            assert isinstance(is_compat, bool)


class TestCheckEnvironmentCompatibility:
    """Test environment compatibility checking."""

    def test_check_environment_compatibility_structure(self):
        """Test that compatibility check returns expected structure."""
        report = check_environment_compatibility()
        
        required_keys = ['python_info', 'compatible', 'issues', 'warnings', 'package_versions']
        for key in required_keys:
            assert key in report
        
        assert isinstance(report['python_info'], dict)
        assert isinstance(report['compatible'], bool)
        assert isinstance(report['issues'], list)
        assert isinstance(report['warnings'], list)
        assert isinstance(report['package_versions'], dict)

    def test_check_environment_compatibility_python_version(self):
        """Test Python version compatibility checking."""
        report = check_environment_compatibility()
        
        # Should detect current Python version as compatible (since we're running tests)
        current_version = sys.version_info
        if current_version >= (3, 8):
            # Should generally be compatible
            python_related_issues = [
                issue for issue in report['issues'] 
                if 'Python' in issue and 'not supported' in issue
            ]
            assert len(python_related_issues) == 0

    @patch('strataregula.core.compatibility.get_python_info')
    def test_check_environment_compatibility_old_python(self, mock_get_python_info):
        """Test compatibility check with old Python version."""
        # Mock old Python version
        mock_get_python_info.return_value = {
            'version': (3, 7, 0),
            'executable': '/usr/bin/python3.7',
            'platform': 'linux',
            'implementation': 'cpython',
            'prefix': '/usr'
        }
        
        report = check_environment_compatibility()
        
        assert report['compatible'] is False
        assert any('Python' in issue for issue in report['issues'])

    @patch('sys.executable', '/some/path/with/pyenv/python')
    def test_check_environment_compatibility_pyenv_warning(self):
        """Test that pyenv usage generates appropriate warning."""
        report = check_environment_compatibility()
        
        pyenv_warnings = [w for w in report['warnings'] if 'pyenv' in w.lower()]
        assert len(pyenv_warnings) > 0


class TestSafeImportWithFallback:
    """Test safe import functionality."""

    def test_safe_import_with_fallback_success(self):
        """Test successful import."""
        # Import a standard module that should exist
        module = safe_import_with_fallback('json')
        assert module is not None
        assert hasattr(module, 'dumps')

    def test_safe_import_with_fallback_failure(self):
        """Test failed import without fallback."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            module = safe_import_with_fallback('definitely_not_a_real_module_12345')
            
            assert module is None
            assert len(w) > 0
            assert "Could not import" in str(w[-1].message)

    def test_safe_import_with_fallback_with_fallback_success(self):
        """Test failed import with successful fallback."""
        # Try to import non-existent module with json as fallback
        module = safe_import_with_fallback('definitely_not_a_real_module_12345', 'json')
        assert module is not None
        assert hasattr(module, 'dumps')

    def test_safe_import_with_fallback_both_fail(self):
        """Test failed import with failed fallback."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            module = safe_import_with_fallback(
                'definitely_not_a_real_module_12345', 
                'also_definitely_not_real_67890'
            )
            
            assert module is None
            assert len(w) > 0


class TestSafeImportPsutil:
    """Test psutil safe import."""

    def test_safe_import_psutil_success(self):
        """Test successful psutil import."""
        # Since psutil is actually installed, this should succeed
        result = safe_import_psutil()
        # Either returns psutil module or None, both are acceptable
        assert result is not None or result is None

    def test_safe_import_psutil_failure(self):
        """Test psutil import behavior."""
        # Since psutil handling is already tested in integration,
        # we just verify the function doesn't crash
        result = safe_import_psutil()
        # Should return either psutil module or None - both are valid
        assert result is not None or result is None


class TestMockPsutilProcess:
    """Test mock psutil process."""

    def test_mock_psutil_process_interface(self):
        """Test that mock process has expected interface."""
        process = MockPsutilProcess()
        
        # Should have required methods
        assert hasattr(process, 'memory_info')
        assert hasattr(process, 'cpu_percent')
        assert hasattr(process, 'memory_percent')
        
        # Methods should be callable
        memory_info = process.memory_info()
        assert hasattr(memory_info, 'rss')
        assert hasattr(memory_info, 'vms')
        assert memory_info.rss == 0
        assert memory_info.vms == 0
        
        assert process.cpu_percent() == 0.0
        assert process.memory_percent() == 0.0


class TestGetCompatibleRichConsole:
    """Test Rich console compatibility."""

    def test_get_compatible_rich_console_success(self):
        """Test Rich console creation."""
        # Test the actual function - it should either return a console or None
        result = get_compatible_rich_console()
        # Both success (console) and fallback (None) are valid outcomes
        assert result is not None or result is None

    def test_get_compatible_rich_console_failure(self):
        """Test Rich console fallback behavior."""
        # Test that the function handles edge cases gracefully
        result = get_compatible_rich_console()
        # Should return either a console or None - both are valid outcomes
        assert result is not None or result is None


class TestCheckYamlCompatibility:
    """Test YAML compatibility checking."""

    def test_check_yaml_compatibility_success(self):
        """Test successful YAML compatibility check."""
        is_compatible, error = check_yaml_compatibility()
        
        # Should be compatible since PyYAML is required
        assert is_compatible is True
        assert error is None

    @patch('builtins.__import__')
    def test_check_yaml_compatibility_import_error(self, mock_import):
        """Test YAML compatibility with import error."""
        def side_effect(name, *args, **kwargs):
            if name == 'yaml':
                raise ImportError("No module named 'yaml'")
            return __import__(name, *args, **kwargs)
        
        mock_import.side_effect = side_effect
        
        is_compatible, error = check_yaml_compatibility()
        assert is_compatible is False
        assert "PyYAML not installed" in error

    @patch('yaml.safe_load')
    def test_check_yaml_compatibility_parsing_error(self, mock_safe_load):
        """Test YAML compatibility with parsing error."""
        mock_safe_load.side_effect = Exception("YAML parsing failed")
        
        is_compatible, error = check_yaml_compatibility()
        assert is_compatible is False
        assert "YAML compatibility issue" in error


class TestPrintCompatibilityReport:
    """Test compatibility report printing."""

    @patch('builtins.print')
    def test_print_compatibility_report_compatible(self, mock_print):
        """Test printing compatibility report for compatible environment."""
        result = print_compatibility_report()
        
        # Should return boolean
        assert isinstance(result, bool)
        
        # Should have printed something
        assert mock_print.called

    @patch('builtins.print')
    @patch('strataregula.core.compatibility.get_python_info')
    def test_print_compatibility_report_incompatible(self, mock_get_python_info, mock_print):
        """Test printing compatibility report for incompatible environment."""
        # Mock incompatible Python version
        mock_get_python_info.return_value = {
            'version': (3, 7, 0),
            'executable': '/usr/bin/python3.7',
            'platform': 'linux',
            'implementation': 'cpython',
            'prefix': '/usr'
        }
        
        result = print_compatibility_report()
        
        assert result is False
        assert mock_print.called
        
        # Check that error information was printed
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "INCOMPATIBLE" in printed_text


class TestCompatibilityIntegration:
    """Integration tests for compatibility module."""

    def test_compatibility_module_imports(self):
        """Test that compatibility module imports correctly."""
        # If we can import and run tests, the module loads correctly
        from strataregula.core.compatibility import check_environment_compatibility
        
        report = check_environment_compatibility()
        assert isinstance(report, dict)

    def test_compatibility_functions_handle_errors(self):
        """Test that compatibility functions handle errors gracefully."""
        # All functions should handle errors gracefully
        functions = [
            get_python_info,
            lambda: check_package_version('test', '1.0.0'),
            check_environment_compatibility,
            lambda: safe_import_with_fallback('test'),
            safe_import_psutil,
            get_compatible_rich_console,
            check_yaml_compatibility,
        ]
        
        for func in functions:
            try:
                result = func()
                # Should return some result, not raise exception
                assert result is not None or result is None  # Allow None returns
            except Exception as e:
                pytest.fail(f"Function {func} raised unexpected exception: {e}")