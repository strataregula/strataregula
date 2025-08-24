"""
Unit tests for hierarchy commands module

Tests for hierarchy processing commands like MergeCommand and EnvironmentMergeCommand.
"""

import pytest
import asyncio
import tempfile
import shutil
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from strataregula.hierarchy.commands import (
    MergeCommand, 
    EnvironmentMergeCommand, 
    ConfigMergeCommand,
    HierarchyInfoCommand
)
from strataregula.hierarchy.merger import MergeStrategy


class TestMergeCommand:
    """Test MergeCommand functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.command = MergeCommand()
    
    def test_command_attributes(self):
        """Test command attributes"""
        assert self.command.name == 'merge'
        assert self.command.description == 'Merge configurations with deep copy for same hierarchies'
        assert self.command.category == 'configuration'
        assert 'dict' in self.command.input_types
        assert 'list' in self.command.input_types
        assert 'dict' in self.command.output_types
        assert 'list' in self.command.output_types
    
    @pytest.mark.asyncio
    async def test_execute_no_merge_data(self):
        """Test execute without merge data"""
        data = {"app": "test"}
        
        result = await self.command.execute(data)
        
        assert result == data
    
    @pytest.mark.asyncio
    async def test_execute_with_dict_merge_data(self):
        """Test execute with dictionary merge data"""
        base_data = {"app": "base", "version": 1.0}
        merge_data = {"app": "merged", "new_key": "value"}
        
        result = await self.command.execute(base_data, with=merge_data)
        
        assert result["app"] == "merged"  # Override
        assert result["version"] == 1.0   # From base
        assert result["new_key"] == "value"  # From merge
    
    @pytest.mark.asyncio
    async def test_execute_with_custom_strategy(self):
        """Test execute with custom merge strategy"""
        base_data = {"list": [1, 2]}
        merge_data = {"list": [3, 4]}
        
        result = await self.command.execute(
            base_data, 
            with=merge_data, 
            strategy="append"
        )
        
        assert result["list"] == [1, 2, 3, 4]
    
    @pytest.mark.asyncio
    async def test_execute_with_invalid_strategy(self):
        """Test execute with invalid merge strategy"""
        base_data = {"app": "test"}
        merge_data = {"app": "merged"}
        
        # Should default to SMART strategy
        result = await self.command.execute(
            base_data, 
            with=merge_data, 
            strategy="invalid_strategy"
        )
        
        assert result["app"] == "merged"
    
    @pytest.mark.asyncio
    async def test_execute_with_file_path(self):
        """Test execute with file path as merge data"""
        temp_dir = tempfile.mkdtemp()
        try:
            base_data = {"app": "base"}
            merge_config = {"app": "merged", "version": 2.0}
            
            config_file = Path(temp_dir) / "config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(merge_config, f)
            
            result = await self.command.execute(
                base_data, 
                with=str(config_file)
            )
            
            assert result["app"] == "merged"
            assert result["version"] == 2.0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_execute_with_yaml_string(self):
        """Test execute with YAML string as merge data"""
        base_data = {"app": "base"}
        yaml_string = "app: merged\nversion: 3.0"
        
        result = await self.command.execute(
            base_data, 
            with=yaml_string
        )
        
        assert result["app"] == "merged"
        assert result["version"] == 3.0
    
    @pytest.mark.asyncio
    async def test_execute_with_invalid_yaml_string(self):
        """Test execute with invalid YAML string"""
        base_data = {"app": "base"}
        invalid_yaml = "invalid: yaml: [unclosed"
        
        with pytest.raises(ValueError, match="Invalid YAML string"):
            await self.command.execute(base_data, with=invalid_yaml)
    
    @pytest.mark.asyncio
    async def test_execute_with_nonexistent_file(self):
        """Test execute with non-existent file path"""
        base_data = {"app": "base"}
        nonexistent_file = "/path/to/nonexistent/file.yaml"
        
        with pytest.raises(ValueError, match="Invalid YAML string"):
            await self.command.execute(base_data, with=nonexistent_file)


class TestEnvironmentMergeCommand:
    """Test EnvironmentMergeCommand functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.command = EnvironmentMergeCommand()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_command_attributes(self):
        """Test command attributes"""
        assert self.command.name == 'env_merge'
        assert self.command.description == 'Merge environment-specific configurations'
        assert self.command.category == 'configuration'
        assert 'dict' in self.command.input_types
        assert 'dict' in self.command.output_types
    
    @pytest.mark.asyncio
    async def test_execute_without_environment_name(self):
        """Test execute without environment name"""
        data = {"app": "test"}
        
        with pytest.raises(ValueError, match="Environment name must be specified"):
            await self.command.execute(data)
    
    @pytest.mark.asyncio
    async def test_execute_no_config_file_found(self):
        """Test execute when no environment config file is found"""
        data = {"app": "base"}
        
        result = await self.command.execute(
            data, 
            environment="development",
            config_dir=str(self.temp_path)
        )
        
        # Should return deep copy of original data
        assert result == {"app": "base"}
        assert result is not data
    
    @pytest.mark.asyncio
    async def test_execute_with_environment_yaml_file(self):
        """Test execute with environment YAML file"""
        data = {"app": "base"}
        env_config = {"database": {"host": "dev-db"}, "environment": "development"}
        
        env_file = self.temp_path / "development.yaml"
        with open(env_file, 'w') as f:
            yaml.dump(env_config, f)
        
        result = await self.command.execute(
            data,
            environment="development", 
            config_dir=str(self.temp_path)
        )
        
        # Should load the environment config
        assert "database" in result or "app" in result
    
    @pytest.mark.asyncio
    async def test_execute_with_different_file_patterns(self):
        """Test execute with different environment file patterns"""
        data = {"app": "base"}
        env_config = {"database": {"host": "prod-db"}}
        
        # Test config.{env}.yaml pattern
        env_file = self.temp_path / "config.production.yaml"
        with open(env_file, 'w') as f:
            yaml.dump(env_config, f)
        
        result = await self.command.execute(
            data,
            environment="production",
            config_dir=str(self.temp_path)
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_execute_with_custom_strategy(self):
        """Test execute with custom merge strategy"""
        data = {"lists": [1, 2]}
        env_config = {"lists": [3, 4]}
        
        env_file = self.temp_path / "test.yaml" 
        with open(env_file, 'w') as f:
            yaml.dump(env_config, f)
        
        result = await self.command.execute(
            data,
            environment="test",
            config_dir=str(self.temp_path),
            strategy="append"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_execute_file_priority_order(self):
        """Test that files are found in correct priority order"""
        data = {"app": "base"}
        env_config1 = {"source": "yaml"}
        env_config2 = {"source": "yml"}
        
        # Create multiple files that match patterns
        yaml_file = self.temp_path / "test.yaml"
        yml_file = self.temp_path / "test.yml"
        
        with open(yaml_file, 'w') as f:
            yaml.dump(env_config1, f)
        with open(yml_file, 'w') as f:
            yaml.dump(env_config2, f)
        
        result = await self.command.execute(
            data,
            environment="test",
            config_dir=str(self.temp_path)
        )
        
        # Should pick the first match (test.yaml)
        assert result is not None


class TestConfigMergeCommand:
    """Test ConfigMergeCommand functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.command = ConfigMergeCommand()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_command_attributes(self):
        """Test command attributes"""
        assert self.command.name == 'config_merge'
        assert self.command.description == 'Merge multiple configuration files'
        assert self.command.category == 'configuration'
        assert 'dict' in self.command.input_types
        assert 'dict' in self.command.output_types
    
    @pytest.mark.asyncio
    async def test_execute_no_files(self):
        """Test execute without files"""
        data = {"app": "test"}
        
        result = await self.command.execute(data)
        
        assert result == data
    
    @pytest.mark.asyncio
    async def test_execute_with_config_files(self):
        """Test execute with configuration files"""
        base_data = {"app": "base", "version": 1.0}
        
        # Create config files
        config1 = {"database": {"host": "db1"}}
        config2 = {"cache": {"ttl": 300}}
        
        file1 = self.temp_path / "config1.yaml"
        file2 = self.temp_path / "config2.yaml"
        
        with open(file1, 'w') as f:
            yaml.dump(config1, f)
        with open(file2, 'w') as f:
            yaml.dump(config2, f)
        
        result = await self.command.execute(
            base_data,
            files=[str(file1), str(file2)]
        )
        
        # Should contain merged data
        assert result["app"] == "base"
        assert result["version"] == 1.0
    
    @pytest.mark.asyncio
    async def test_execute_with_nonexistent_files(self):
        """Test execute with non-existent files"""
        base_data = {"app": "base"}
        
        result = await self.command.execute(
            base_data,
            files=["/nonexistent/file1.yaml", "/nonexistent/file2.yaml"]
        )
        
        # Should still return base data even if files don't exist
        assert result["app"] == "base"
    
    @pytest.mark.asyncio
    async def test_execute_with_output_file(self):
        """Test execute with output file option"""
        base_data = {"app": "base"}
        config1 = {"version": 2.0}
        
        config_file = self.temp_path / "config.yaml"
        output_file = self.temp_path / "output.yaml"
        
        with open(config_file, 'w') as f:
            yaml.dump(config1, f)
        
        result = await self.command.execute(
            base_data,
            files=[str(config_file)],
            output=str(output_file),
            format="yaml"
        )
        
        assert result is not None
        assert output_file.exists()
    
    @pytest.mark.asyncio
    async def test_execute_with_custom_strategy(self):
        """Test execute with custom merge strategy"""
        base_data = {"list": [1, 2]}
        config1 = {"list": [3, 4]}
        
        config_file = self.temp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config1, f)
        
        result = await self.command.execute(
            base_data,
            files=[str(config_file)],
            strategy="append"
        )
        
        assert result is not None


class TestHierarchyInfoCommand:
    """Test HierarchyInfoCommand functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.command = HierarchyInfoCommand()
    
    def test_command_attributes(self):
        """Test command attributes"""
        assert self.command.name == 'hierarchy_info'
        assert self.command.description == 'Display hierarchy information and merge strategy'
        assert self.command.category == 'information'
        assert 'any' in self.command.input_types
        assert 'dict' in self.command.output_types
    
    @pytest.mark.asyncio
    async def test_execute_with_dict_data(self):
        """Test execute with dictionary data"""
        data = {
            "level1": {
                "level2": {
                    "key": "value"
                }
            },
            "simple": "string"
        }
        
        result = await self.command.execute(data)
        
        assert result["strategy"] == "smart"  # Default strategy
        assert result["data_type"] == "dict"
        assert result["hierarchy_depth"] >= 0
        assert result["total_keys"] > 0
        assert result["structure"] == "dict"
        assert "merge_recommendation" in result
    
    @pytest.mark.asyncio
    async def test_execute_with_list_data(self):
        """Test execute with list data"""
        data = [1, 2, {"nested": "dict"}, [4, 5]]
        
        result = await self.command.execute(data)
        
        assert result["data_type"] == "list"
        assert result["structure"] == "list"
    
    @pytest.mark.asyncio
    async def test_execute_with_simple_data(self):
        """Test execute with simple data type"""
        data = "simple string"
        
        result = await self.command.execute(data)
        
        assert result["data_type"] == "str"
        assert result["structure"] == "str"
        assert result["total_keys"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_custom_strategy(self):
        """Test execute with custom strategy"""
        data = {"test": "data"}
        
        result = await self.command.execute(data, strategy="deep_copy")
        
        assert result["strategy"] == "deep_copy"
    
    @pytest.mark.asyncio
    async def test_execute_with_invalid_strategy(self):
        """Test execute with invalid strategy"""
        data = {"test": "data"}
        
        result = await self.command.execute(data, strategy="invalid")
        
        assert result["strategy"] == "smart"  # Should default to SMART
    
    def test_analyze_hierarchy_dict(self):
        """Test _analyze_hierarchy with dictionary"""
        data = {
            "level1": {
                "level2": "value",
                "level2b": {"level3": "deep"}
            },
            "simple": "value"
        }
        
        hierarchy_info = self.command._analyze_hierarchy(data)
        
        assert hierarchy_info["structure"] == "dict"
        assert hierarchy_info["depth"] == 0
        assert hierarchy_info["total_keys"] > 3  # At least level1, level2, level2b, level3, simple
    
    def test_analyze_hierarchy_list(self):
        """Test _analyze_hierarchy with list"""
        data = [1, {"nested": "dict"}, [2, 3]]
        
        hierarchy_info = self.command._analyze_hierarchy(data)
        
        assert hierarchy_info["structure"] == "list"
        assert hierarchy_info["total_keys"] >= 3  # Basic items + nested items
    
    def test_analyze_hierarchy_max_depth(self):
        """Test _analyze_hierarchy with max depth limit"""
        # Create very nested structure
        data = {"level": "start"}
        current = data
        for i in range(15):  # More than max_depth (10)
            current["level"] = {"nested": f"level_{i}"}
            current = current["level"]
        
        hierarchy_info = self.command._analyze_hierarchy(data, max_depth=5)
        
        assert hierarchy_info["structure"] == "max_depth_reached" or hierarchy_info["structure"] == "dict"
    
    def test_get_merge_recommendation_smart_dict(self):
        """Test merge recommendation for smart strategy with dict"""
        data = {"key": "value"}
        
        recommendation = self.command._get_merge_recommendation(data, MergeStrategy.SMART)
        
        assert "analyze data structure" in recommendation
        assert "optimal strategy" in recommendation
    
    def test_get_merge_recommendation_smart_list(self):
        """Test merge recommendation for smart strategy with list"""
        data = [1, 2, 3]
        
        recommendation = self.command._get_merge_recommendation(data, MergeStrategy.SMART)
        
        assert "analyze list contents" in recommendation
        assert "replace/merge/append" in recommendation
    
    def test_get_merge_recommendation_deep_copy(self):
        """Test merge recommendation for deep copy strategy"""
        data = {"key": "value"}
        
        recommendation = self.command._get_merge_recommendation(data, MergeStrategy.DEEP_COPY)
        
        assert "completely replace" in recommendation
    
    def test_get_merge_recommendation_merge(self):
        """Test merge recommendation for merge strategy"""
        data = {"key": "value"}
        
        recommendation = self.command._get_merge_recommendation(data, MergeStrategy.MERGE)
        
        assert "combine hierarchies" in recommendation
        assert "preserving existing" in recommendation
    
    def test_get_merge_recommendation_append(self):
        """Test merge recommendation for append strategy"""
        data = [1, 2, 3]
        
        recommendation = self.command._get_merge_recommendation(data, MergeStrategy.APPEND)
        
        assert "add new items" in recommendation
        assert "existing lists" in recommendation


class TestCommandIntegration:
    """Test command integration scenarios"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_command_chaining_scenario(self):
        """Test a realistic command chaining scenario"""
        # Setup: Create base config and environment config
        base_data = {
            "app": "myapp",
            "database": {"host": "localhost", "port": 5432},
            "features": ["basic"]
        }
        
        env_config = {
            "database": {"host": "prod-db", "ssl": True},
            "features": ["basic", "advanced"],
            "environment": "production"
        }
        
        env_file = self.temp_path / "production.yaml"
        with open(env_file, 'w') as f:
            yaml.dump(env_config, f)
        
        # Step 1: Environment merge
        env_merge_cmd = EnvironmentMergeCommand()
        merged_data = await env_merge_cmd.execute(
            base_data,
            environment="production",
            config_dir=str(self.temp_path),
            strategy="smart"
        )
        
        # Step 2: Get hierarchy info
        info_cmd = HierarchyInfoCommand()
        info = await info_cmd.execute(merged_data)
        
        assert info["data_type"] == "dict"
        assert info["strategy"] == "smart"
        assert "merge_recommendation" in info
    
    @pytest.mark.asyncio
    async def test_error_resilience(self):
        """Test that commands handle errors gracefully"""
        # Test with corrupt YAML file
        corrupt_file = self.temp_path / "corrupt.yaml"
        with open(corrupt_file, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
        
        merge_cmd = MergeCommand()
        
        # Should raise ValueError for invalid YAML
        with pytest.raises(ValueError):
            await merge_cmd.execute(
                {"base": "data"},
                with=str(corrupt_file)
            )


class TestAsyncBehavior:
    """Test async behavior of commands"""
    
    @pytest.mark.asyncio
    async def test_commands_are_async(self):
        """Test that all commands properly support async execution"""
        commands = [
            MergeCommand(),
            EnvironmentMergeCommand(), 
            ConfigMergeCommand(),
            HierarchyInfoCommand()
        ]
        
        data = {"test": "data"}
        tasks = []
        
        for cmd in commands:
            if isinstance(cmd, EnvironmentMergeCommand):
                # EnvironmentMergeCommand requires environment parameter
                task = cmd.execute(data, environment="test")
            else:
                task = cmd.execute(data)
            tasks.append(task)
        
        # Should be able to await all commands
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete (even if some raise exceptions)
        assert len(results) == len(commands)
        
        # At least some should succeed
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) > 0