"""
Tests for plugins builtin module
"""

import pytest
from unittest.mock import Mock, patch

from strataregula.plugins.builtin import (
    RegionPlugin, SimulationPlugin, ProcessPlugin, 
    ResourcePlugin, EnvironmentPlugin, SimulationPlugins
)
from strataregula.plugins.base import PluginInfo, PatternPlugin


class TestRegionPlugin:
    """Test RegionPlugin class"""

    def test_region_plugin_info(self):
        """Test RegionPlugin info property"""
        plugin = RegionPlugin()
        info = plugin.info
        
        assert isinstance(info, PluginInfo)
        assert info.name == "RegionPlugin"
        assert info.version == "1.0.0"
        assert "Japanese prefectures" in info.description

    def test_region_plugin_can_handle(self):
        """Test RegionPlugin can_handle method"""
        plugin = RegionPlugin()
        
        # Should handle patterns with * and region keywords
        assert plugin.can_handle("server_*_region") is True
        assert plugin.can_handle("*_prefecture_data") is True
        assert plugin.can_handle("Region_*_config") is True  # Case insensitive
        assert plugin.can_handle("PREFECTURE_*_settings") is True
        
        # Should not handle patterns without * or region keywords
        assert plugin.can_handle("server_region") is False  # No *
        assert plugin.can_handle("*_server_data") is False  # No region keywords
        assert plugin.can_handle("simple_pattern") is False

    def test_region_plugin_expand_default_prefectures(self):
        """Test RegionPlugin expand with default prefectures"""
        plugin = RegionPlugin()
        context = {"value": 100}
        
        result = plugin.expand("server_*_region", context)
        
        # Check that all 47 prefectures are included
        assert len(result) == 47
        
        # Check specific prefectures
        assert "server_tokyo_region" in result
        assert "server_osaka_region" in result
        assert "server_hokkaido_region" in result
        assert "server_okinawa_region" in result
        
        # Check all values are set correctly
        assert all(value == 100 for value in result.values())

    def test_region_plugin_expand_custom_prefectures(self):
        """Test RegionPlugin expand with custom prefectures from context"""
        plugin = RegionPlugin()
        context = {
            "value": 50,
            "data_sources": {
                "prefectures": ["tokyo", "osaka", "fukuoka"]
            }
        }
        
        result = plugin.expand("*_server", context)
        
        # Should use custom prefectures
        assert len(result) == 3
        assert "tokyo_server" in result
        assert "osaka_server" in result
        assert "fukuoka_server" in result
        
        # Check values
        assert all(value == 50 for value in result.values())

    def test_region_plugin_expand_default_value(self):
        """Test RegionPlugin expand with default value"""
        plugin = RegionPlugin()
        context = {"data_sources": {"prefectures": ["test1", "test2"]}}
        
        result = plugin.expand("*_pattern", context)
        
        # Should use default value of 0
        assert all(value == 0 for value in result.values())


class TestSimulationPlugin:
    """Test SimulationPlugin class"""

    def test_simulation_plugin_info(self):
        """Test SimulationPlugin info property"""
        plugin = SimulationPlugin()
        info = plugin.info
        
        assert isinstance(info, PluginInfo)
        assert info.name == "SimulationPlugin"
        assert info.version == "1.0.0"
        assert "simulation patterns" in info.description

    def test_simulation_plugin_can_handle(self):
        """Test SimulationPlugin can_handle method"""
        plugin = SimulationPlugin()
        
        # Should handle patterns with * and simulation keywords
        assert plugin.can_handle("*_simulation") is True
        assert plugin.can_handle("scenario_*_test") is True
        assert plugin.can_handle("MODEL_*_config") is True  # Case insensitive
        assert plugin.can_handle("*_test_data") is True
        assert plugin.can_handle("demo_*_setup") is True
        
        # Should not handle patterns without * or simulation keywords
        assert plugin.can_handle("simulation") is False  # No *
        assert plugin.can_handle("*_server") is False  # No simulation keywords

    def test_simulation_plugin_expand(self):
        """Test SimulationPlugin expand method"""
        plugin = SimulationPlugin()
        context = {"value": 75}
        
        result = plugin.expand("*_simulation", context)
        
        # Should expand to all simulation types
        expected_keys = ["basic_simulation", "advanced_simulation", 
                        "custom_simulation", "production_simulation"]
        
        assert len(result) == 4
        for key in expected_keys:
            assert key in result
            assert result[key] == 75


class TestProcessPlugin:
    """Test ProcessPlugin class"""

    def test_process_plugin_info(self):
        """Test ProcessPlugin info property"""
        plugin = ProcessPlugin()
        info = plugin.info
        
        assert isinstance(info, PluginInfo)
        assert info.name == "ProcessPlugin"
        assert info.version == "1.0.0"
        assert "process patterns" in info.description

    def test_process_plugin_can_handle(self):
        """Test ProcessPlugin can_handle method"""
        plugin = ProcessPlugin()
        
        # Should handle patterns with * and process keywords
        assert plugin.can_handle("*_process") is True
        assert plugin.can_handle("workflow_*_config") is True
        assert plugin.can_handle("STEP_*_data") is True  # Case insensitive
        assert plugin.can_handle("*_stage_setup") is True
        assert plugin.can_handle("phase_*_execution") is True
        
        # Should not handle patterns without appropriate keywords
        assert plugin.can_handle("*_server") is False

    def test_process_plugin_expand(self):
        """Test ProcessPlugin expand method"""
        plugin = ProcessPlugin()
        context = {"value": 25}
        
        result = plugin.expand("workflow_*", context)
        
        # Should expand to all process stages
        expected_keys = ["workflow_start", "workflow_process", 
                        "workflow_review", "workflow_complete"]
        
        assert len(result) == 4
        for key in expected_keys:
            assert key in result
            assert result[key] == 25


class TestResourcePlugin:
    """Test ResourcePlugin class"""

    def test_resource_plugin_info(self):
        """Test ResourcePlugin info property"""
        plugin = ResourcePlugin()
        info = plugin.info
        
        assert isinstance(info, PluginInfo)
        assert info.name == "ResourcePlugin"
        assert info.version == "1.0.0"
        assert "resource allocation" in info.description

    def test_resource_plugin_can_handle(self):
        """Test ResourcePlugin can_handle method"""
        plugin = ResourcePlugin()
        
        # Should handle patterns with * and resource keywords
        assert plugin.can_handle("*_cpu") is True
        assert plugin.can_handle("memory_*_allocation") is True
        assert plugin.can_handle("STORAGE_*_config") is True  # Case insensitive
        assert plugin.can_handle("*_network_setup") is True
        assert plugin.can_handle("resource_*_pool") is True
        
        # Should not handle patterns without resource keywords
        assert plugin.can_handle("*_server") is False

    def test_resource_plugin_expand(self):
        """Test ResourcePlugin expand method"""
        plugin = ResourcePlugin()
        context = {"value": 10}
        
        result = plugin.expand("*_cpu_allocation", context)
        
        # Should expand to all resource sizes
        expected_keys = ["xs_cpu_allocation", "s_cpu_allocation", 
                        "m_cpu_allocation", "l_cpu_allocation", "xl_cpu_allocation"]
        
        assert len(result) == 5
        for key in expected_keys:
            assert key in result
            assert result[key] == 10


class TestEnvironmentPlugin:
    """Test EnvironmentPlugin class"""

    def test_environment_plugin_info(self):
        """Test EnvironmentPlugin info property"""
        plugin = EnvironmentPlugin()
        info = plugin.info
        
        assert isinstance(info, PluginInfo)
        assert info.name == "EnvironmentPlugin"
        assert info.version == "1.0.0"
        assert "environment-specific" in info.description

    def test_environment_plugin_can_handle(self):
        """Test EnvironmentPlugin can_handle method"""
        plugin = EnvironmentPlugin()
        
        # Should handle patterns with * and environment keywords
        assert plugin.can_handle("*_env") is True
        assert plugin.can_handle("environment_*_config") is True
        assert plugin.can_handle("STAGE_*_setup") is True  # Case insensitive
        
        # Should not handle patterns without environment keywords
        assert plugin.can_handle("*_server") is False

    def test_environment_plugin_expand(self):
        """Test EnvironmentPlugin expand method"""
        plugin = EnvironmentPlugin()
        context = {"value": 5}
        
        result = plugin.expand("*_environment", context)
        
        # Should expand to all environments
        expected_keys = ["dev_environment", "staging_environment", 
                        "prod_environment", "dr_environment"]
        
        assert len(result) == 4
        for key in expected_keys:
            assert key in result
            assert result[key] == 5


class TestSimulationPlugins:
    """Test SimulationPlugins collection class"""

    def test_get_all_plugins(self):
        """Test getting all simulation plugins"""
        plugins = SimulationPlugins.get_all_plugins()
        
        # Should return all 5 built-in plugins
        assert len(plugins) == 5
        
        # Check types
        plugin_types = [type(plugin).__name__ for plugin in plugins]
        expected_types = ["RegionPlugin", "SimulationPlugin", "ProcessPlugin", 
                         "ResourcePlugin", "EnvironmentPlugin"]
        
        for expected_type in expected_types:
            assert expected_type in plugin_types
        
        # Check all are PatternPlugin instances
        assert all(isinstance(plugin, PatternPlugin) for plugin in plugins)

    def test_get_all_plugins_are_unique_instances(self):
        """Test that get_all_plugins returns new instances each time"""
        plugins1 = SimulationPlugins.get_all_plugins()
        plugins2 = SimulationPlugins.get_all_plugins()
        
        # Should be different instances
        for p1, p2 in zip(plugins1, plugins2):
            assert p1 is not p2
            assert type(p1) == type(p2)

    def test_register_all(self):
        """Test registering all plugins with a manager"""
        # Mock plugin manager
        mock_manager = Mock()
        
        SimulationPlugins.register_all(mock_manager)
        
        # Should have called register_plugin 5 times
        assert mock_manager.register_plugin.call_count == 5
        
        # Check that correct plugin types were registered
        registered_plugins = [call[0][0] for call in mock_manager.register_plugin.call_args_list]
        plugin_types = [type(plugin).__name__ for plugin in registered_plugins]
        
        expected_types = ["RegionPlugin", "SimulationPlugin", "ProcessPlugin", 
                         "ResourcePlugin", "EnvironmentPlugin"]
        
        for expected_type in expected_types:
            assert expected_type in plugin_types

    def test_all_plugins_can_handle_different_patterns(self):
        """Test that different plugins handle different patterns"""
        plugins = SimulationPlugins.get_all_plugins()
        
        # Test patterns that should be handled by specific plugins
        test_cases = [
            ("*_region", "RegionPlugin"),
            ("*_simulation", "SimulationPlugin"), 
            ("*_process", "ProcessPlugin"),
            ("*_cpu", "ResourcePlugin"),
            ("*_env", "EnvironmentPlugin")
        ]
        
        for pattern, expected_plugin_type in test_cases:
            handling_plugins = [p for p in plugins if p.can_handle(pattern)]
            
            # At least one plugin should handle each pattern
            assert len(handling_plugins) >= 1
            
            # The expected plugin should be among them
            handling_plugin_types = [type(p).__name__ for p in handling_plugins]
            assert expected_plugin_type in handling_plugin_types

    def test_plugins_expand_consistently(self):
        """Test that plugins expand patterns consistently"""
        plugins = SimulationPlugins.get_all_plugins()
        
        for plugin in plugins:
            context = {"value": 123}
            
            # Find a pattern this plugin can handle
            test_pattern = "*_test"
            if plugin.can_handle(test_pattern):
                result = plugin.expand(test_pattern, context)
                
                # Result should be a dictionary
                assert isinstance(result, dict)
                
                # All values should match the context value
                assert all(value == 123 for value in result.values())
                
                # All keys should contain the expanded pattern
                assert all("test" in key for key in result.keys())