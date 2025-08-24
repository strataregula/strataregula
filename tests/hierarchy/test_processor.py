"""
Unit tests for hierarchy processor module

Tests for HierarchyProcessor class and configuration management.
"""

import pytest
import yaml
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock

from strataregula.hierarchy.processor import HierarchyProcessor
from strataregula.hierarchy.merger import MergeStrategy


class TestHierarchyProcessorInit:
    """Test HierarchyProcessor initialization"""
    
    def test_init_default_strategy(self):
        """Test default initialization"""
        processor = HierarchyProcessor()
        
        assert processor.merger.strategy == MergeStrategy.SMART
        assert processor.environment_configs == {}
        assert processor.base_config is None
    
    def test_init_custom_strategy(self):
        """Test initialization with custom strategy"""
        processor = HierarchyProcessor(MergeStrategy.DEEP_COPY)
        
        assert processor.merger.strategy == MergeStrategy.DEEP_COPY
    
    @patch('strataregula.hierarchy.processor.logger')
    def test_init_logging(self, mock_logger):
        """Test logging during initialization"""
        HierarchyProcessor(MergeStrategy.MERGE)
        
        mock_logger.info.assert_called_with(
            "Initialized HierarchyProcessor with strategy: merge"
        )


class TestConfigLoading:
    """Test configuration loading functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = HierarchyProcessor()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_base_config_success(self):
        """Test successful base config loading"""
        config_data = {"app": "test", "version": "1.0"}
        config_file = self.temp_path / "config.yaml"
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        result = self.processor.load_base_config(config_file)
        
        assert result is True
        assert self.processor.base_config == config_data
    
    def test_load_base_config_file_not_found(self):
        """Test base config loading with missing file"""
        non_existent_file = self.temp_path / "missing.yaml"
        
        result = self.processor.load_base_config(non_existent_file)
        
        assert result is False
        assert self.processor.base_config is None
    
    def test_load_base_config_yaml_error(self):
        """Test base config loading with invalid YAML"""
        config_file = self.temp_path / "invalid.yaml"
        
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
        
        result = self.processor.load_base_config(config_file)
        
        assert result is False
        assert self.processor.base_config is None
    
    def test_load_base_config_string_path(self):
        """Test base config loading with string path"""
        config_data = {"test": "data"}
        config_file = self.temp_path / "config.yaml"
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        result = self.processor.load_base_config(str(config_file))
        
        assert result is True
        assert self.processor.base_config == config_data
    
    @patch('strataregula.hierarchy.processor.logger')
    def test_load_base_config_logging(self, mock_logger):
        """Test logging during base config loading"""
        config_file = self.temp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({"test": "data"}, f)
        
        self.processor.load_base_config(config_file)
        
        mock_logger.info.assert_called_with(f"Loaded base config from: {config_file}")


class TestEnvironmentConfigLoading:
    """Test environment-specific configuration loading"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = HierarchyProcessor()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_environment_config_success(self):
        """Test successful environment config loading"""
        config_data = {"database": {"host": "prod-db"}}
        config_file = self.temp_path / "prod.yaml"
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        result = self.processor.load_environment_config("production", config_file)
        
        assert result is True
        assert "production" in self.processor.environment_configs
        expected_config = {**config_data, "environment": "production"}
        assert self.processor.environment_configs["production"] == expected_config
    
    def test_load_environment_config_file_not_found(self):
        """Test environment config loading with missing file"""
        non_existent_file = self.temp_path / "missing.yaml"
        
        result = self.processor.load_environment_config("test", non_existent_file)
        
        assert result is False
        assert "test" not in self.processor.environment_configs
    
    def test_load_environment_config_multiple_environments(self):
        """Test loading multiple environment configs"""
        dev_config = {"database": {"host": "dev-db"}}
        prod_config = {"database": {"host": "prod-db"}}
        
        dev_file = self.temp_path / "dev.yaml"
        prod_file = self.temp_path / "prod.yaml"
        
        with open(dev_file, 'w') as f:
            yaml.dump(dev_config, f)
        with open(prod_file, 'w') as f:
            yaml.dump(prod_config, f)
        
        dev_result = self.processor.load_environment_config("development", dev_file)
        prod_result = self.processor.load_environment_config("production", prod_file)
        
        assert dev_result is True
        assert prod_result is True
        assert len(self.processor.environment_configs) == 2
        assert "development" in self.processor.environment_configs
        assert "production" in self.processor.environment_configs


class TestMultipleConfigLoading:
    """Test loading multiple configuration files"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = HierarchyProcessor()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_multiple_configs_success(self):
        """Test successful loading of multiple configs"""
        base_config = {"app": "test", "version": "1.0"}
        env_config = {"database": {"host": "localhost"}, "environment": "dev"}
        
        base_file = self.temp_path / "base.yaml"
        env_file = self.temp_path / "env.yaml"
        
        with open(base_file, 'w') as f:
            yaml.dump(base_config, f)
        with open(env_file, 'w') as f:
            yaml.dump(env_config, f)
        
        result = self.processor.load_multiple_configs([base_file, env_file])
        
        assert result is True
        assert self.processor.base_config == base_config
        assert "dev" in self.processor.environment_configs
    
    def test_load_multiple_configs_empty_list(self):
        """Test loading multiple configs with empty list"""
        result = self.processor.load_multiple_configs([])
        
        assert result is False
    
    def test_load_multiple_configs_some_missing(self):
        """Test loading multiple configs with some missing files"""
        valid_config = {"app": "test"}
        valid_file = self.temp_path / "valid.yaml"
        missing_file = self.temp_path / "missing.yaml"
        
        with open(valid_file, 'w') as f:
            yaml.dump(valid_config, f)
        
        result = self.processor.load_multiple_configs([valid_file, missing_file])
        
        assert result is True  # Should succeed with at least one valid file
        assert self.processor.base_config == valid_config
    
    def test_load_multiple_configs_auto_environment_names(self):
        """Test automatic environment name generation"""
        config1 = {"app": "test1"}
        config2 = {"app": "test2"}  # No explicit environment
        config3 = {"app": "test3", "environment": "explicit"}
        
        files = []
        for i, config in enumerate([config1, config2, config3], 1):
            config_file = self.temp_path / f"config{i}.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config, f)
            files.append(config_file)
        
        result = self.processor.load_multiple_configs(files)
        
        assert result is True
        assert "config_1" in self.processor.environment_configs  # Auto-generated name
        assert "explicit" in self.processor.environment_configs  # Explicit name


class TestConfigMerging:
    """Test configuration merging functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = HierarchyProcessor()
        self.processor.base_config = {"app": "test", "version": "1.0"}
        self.processor.environment_configs = {
            "development": {
                "database": {"host": "dev-db"},
                "environment": "development"
            },
            "production": {
                "database": {"host": "prod-db", "ssl": True},
                "environment": "production"
            }
        }
    
    def test_get_merged_config_no_base(self):
        """Test get_merged_config without base config"""
        processor = HierarchyProcessor()
        result = processor.get_merged_config()
        
        assert result is None
    
    def test_get_merged_config_specific_environment(self):
        """Test getting merged config for specific environment"""
        result = self.processor.get_merged_config("development")
        
        expected = {
            "app": "test",
            "version": "1.0",
            "database": {"host": "dev-db"},
            "environment": "development"
        }
        # Compare key structure
        assert set(result.keys()) == set(expected.keys())
        assert result["app"] == expected["app"]
        assert result["database"]["host"] == expected["database"]["host"]
    
    def test_get_merged_config_nonexistent_environment(self):
        """Test getting merged config for non-existent environment"""
        result = self.processor.get_merged_config("staging")
        
        # Should return base config when environment doesn't exist
        expected_keys = set(self.processor.base_config.keys())
        assert set(result.keys()) >= expected_keys
    
    def test_get_merged_config_all_environments(self):
        """Test getting merged config with all environments"""
        result = self.processor.get_merged_config()
        
        # Should contain base config and merged environment configs
        assert "app" in result
        assert "version" in result
    
    def test_get_merged_config_custom_strategy(self):
        """Test getting merged config with custom strategy"""
        result = self.processor.get_merged_config("development", MergeStrategy.DEEP_COPY)
        
        # Strategy should be applied
        assert self.processor.merger.strategy == MergeStrategy.DEEP_COPY
        assert result is not None
    
    def test_merge_configs_empty_list(self):
        """Test merging empty config list"""
        result = self.processor.merge_configs([])
        
        assert result is None
    
    def test_merge_configs_success(self):
        """Test successful config merging"""
        configs = [
            {"a": 1, "common": "base"},
            {"b": 2, "common": "override"}
        ]
        
        result = self.processor.merge_configs(configs)
        
        expected = {"a": 1, "b": 2, "common": "override"}
        assert result == expected
    
    def test_merge_configs_custom_strategy(self):
        """Test merging configs with custom strategy"""
        configs = [{"list": [1, 2]}, {"list": [3, 4]}]
        
        result = self.processor.merge_configs(configs, MergeStrategy.APPEND)
        
        assert result["list"] == [1, 2, 3, 4]


class TestConfigSaving:
    """Test configuration saving functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = HierarchyProcessor()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_merged_config_yaml(self):
        """Test saving merged config as YAML"""
        config = {"app": "test", "version": 1.0}
        output_file = self.temp_path / "output.yaml"
        
        result = self.processor.save_merged_config(config, output_file, "yaml")
        
        assert result is True
        assert output_file.exists()
        
        # Verify content
        with open(output_file) as f:
            loaded_config = yaml.safe_load(f)
        assert loaded_config == config
    
    def test_save_merged_config_json(self):
        """Test saving merged config as JSON"""
        config = {"app": "test", "version": 1.0}
        output_file = self.temp_path / "output.json"
        
        result = self.processor.save_merged_config(config, output_file, "json")
        
        assert result is True
        assert output_file.exists()
        
        # Verify content
        with open(output_file) as f:
            loaded_config = json.load(f)
        assert loaded_config == config
    
    def test_save_merged_config_unsupported_format(self):
        """Test saving merged config with unsupported format"""
        config = {"app": "test"}
        output_file = self.temp_path / "output.xml"
        
        result = self.processor.save_merged_config(config, output_file, "xml")
        
        assert result is False
    
    def test_save_merged_config_creates_directories(self):
        """Test that save_merged_config creates parent directories"""
        config = {"app": "test"}
        nested_dir = self.temp_path / "nested" / "deep"
        output_file = nested_dir / "output.yaml"
        
        result = self.processor.save_merged_config(config, output_file, "yaml")
        
        assert result is True
        assert output_file.exists()
        assert nested_dir.exists()
    
    def test_save_merged_config_string_path(self):
        """Test saving merged config with string path"""
        config = {"app": "test"}
        output_file = str(self.temp_path / "output.yaml")
        
        result = self.processor.save_merged_config(config, output_file, "yaml")
        
        assert result is True
        assert Path(output_file).exists()


class TestUtilityMethods:
    """Test utility methods"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = HierarchyProcessor()
        self.processor.environment_configs = {
            "development": {"env": "dev"},
            "production": {"env": "prod"},
            "staging": {"env": "stage"}
        }
    
    def test_get_available_environments(self):
        """Test getting available environments"""
        environments = self.processor.get_available_environments()
        
        expected = ["development", "production", "staging"]
        assert set(environments) == set(expected)
    
    def test_get_available_environments_empty(self):
        """Test getting available environments when none exist"""
        processor = HierarchyProcessor()
        environments = processor.get_available_environments()
        
        assert environments == []
    
    def test_get_config_summary_with_base(self):
        """Test getting config summary with base config"""
        self.processor.base_config = {"app": "test", "version": 1.0}
        
        summary = self.processor.get_config_summary()
        
        assert summary["base_config_loaded"] is True
        assert set(summary["base_config_keys"]) == {"app", "version"}
        assert len(summary["environments"]) == 3
        assert summary["total_configs"] == 4  # 1 base + 3 env
        assert "base_config_size" in summary
    
    def test_get_config_summary_without_base(self):
        """Test getting config summary without base config"""
        processor = HierarchyProcessor()
        processor.environment_configs = {"test": {"env": "test"}}
        
        summary = processor.get_config_summary()
        
        assert summary["base_config_loaded"] is False
        assert summary["base_config_keys"] == []
        assert summary["total_configs"] == 1  # 0 base + 1 env
    
    def test_clear_configs(self):
        """Test clearing all configurations"""
        self.processor.base_config = {"app": "test"}
        
        self.processor.clear_configs()
        
        assert self.processor.base_config is None
        assert self.processor.environment_configs == {}


class TestValidation:
    """Test configuration validation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = HierarchyProcessor()
    
    def test_validate_configs_with_valid_configs(self):
        """Test validating valid configurations"""
        self.processor.base_config = {"app": "test"}
        self.processor.environment_configs = {
            "development": {"database": {"host": "dev"}, "environment": "development"},
            "production": {"database": {"host": "prod"}, "environment": "production"}
        }
        
        results = self.processor.validate_configs()
        
        assert results["base_config"] is True
        assert results["env_development"] is True
        assert results["env_production"] is True
    
    def test_validate_configs_no_configs(self):
        """Test validating when no configs are loaded"""
        results = self.processor.validate_configs()
        
        assert len(results) == 0
    
    def test_validate_single_config_valid_dict(self):
        """Test validating single valid config"""
        config = {"app": "test", "version": 1.0}
        
        result = self.processor._validate_single_config(config)
        
        assert result is True
    
    def test_validate_single_config_with_environment(self):
        """Test validating config with environment"""
        config = {"app": "test", "environment": "production"}
        
        result = self.processor._validate_single_config(config)
        
        assert result is True
    
    def test_validate_single_config_invalid_environment(self):
        """Test validating config with invalid environment"""
        config = {"app": "test", "environment": ""}  # Empty environment
        
        result = self.processor._validate_single_config(config)
        
        assert result is False
    
    def test_validate_single_config_non_dict(self):
        """Test validating non-dictionary config"""
        config = ["not", "a", "dict"]
        
        result = self.processor._validate_single_config(config)
        
        assert result is False
    
    def test_validate_single_config_exception_handling(self):
        """Test validation with exception handling"""
        # Mock config that raises exception during validation
        config = Mock()
        config.__contains__ = Mock(side_effect=Exception("Test exception"))
        
        result = self.processor._validate_single_config(config)
        
        assert result is False


class TestConflictResolution:
    """Test conflict resolution functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = HierarchyProcessor()
    
    def test_resolve_config_conflicts_basic(self):
        """Test basic conflict resolution"""
        base = {"app": "base", "version": 1.0}
        conflicts = [
            {"app": "conflict1", "priority": "low"},
            {"app": "conflict2", "priority": "high"}
        ]
        priority_order = ["high", "low"]
        
        result = self.processor.resolve_config_conflicts(base, conflicts, priority_order)
        
        # High priority should win
        assert result["app"] == "conflict2"
        assert result["priority"] == "high"
        assert result["version"] == 1.0  # From base
    
    def test_resolve_config_conflicts_empty_conflicts(self):
        """Test conflict resolution with no conflicts"""
        base = {"app": "base"}
        
        result = self.processor.resolve_config_conflicts(base, [])
        
        assert result == {"app": "base"}
        assert result is not base  # Should be deep copied


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = HierarchyProcessor()
    
    @patch('strataregula.hierarchy.processor.logger')
    def test_load_base_config_exception_handling(self, mock_logger):
        """Test base config loading exception handling"""
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = self.processor.load_base_config("dummy_path")
        
        assert result is False
        assert self.processor.base_config is None
        mock_logger.error.assert_called()
    
    @patch('strataregula.hierarchy.processor.logger')
    def test_save_config_exception_handling(self, mock_logger):
        """Test save config exception handling"""
        config = {"app": "test"}
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = self.processor.save_merged_config(config, "dummy_path", "yaml")
        
        assert result is False
        mock_logger.error.assert_called()


class TestLogging:
    """Test logging functionality"""
    
    @patch('strataregula.hierarchy.processor.logger')
    def test_various_logging_calls(self, mock_logger):
        """Test that various operations produce appropriate logging"""
        processor = HierarchyProcessor()
        
        # Test config summary logging is part of the workflow
        processor.base_config = {"test": "data"}
        processor.get_config_summary()
        
        # Test clear configs logging
        processor.clear_configs()
        
        mock_logger.info.assert_called_with("Cleared all configurations")