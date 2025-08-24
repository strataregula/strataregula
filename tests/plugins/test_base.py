"""
Tests for plugins base module
"""

import pytest
from unittest.mock import Mock, patch

from strataregula.plugins.base import PluginInfo, PatternPlugin, PluginManager


class TestPluginInfo:
    """Test PluginInfo dataclass"""

    def test_plugin_info_creation(self):
        """Test creating PluginInfo"""
        info = PluginInfo(
            name="TestPlugin",
            version="1.0.0",
            description="Test plugin description"
        )
        
        assert info.name == "TestPlugin"
        assert info.version == "1.0.0"
        assert info.description == "Test plugin description"


class TestPatternPlugin:
    """Test PatternPlugin abstract class"""

    def create_test_plugin(self):
        """Create a concrete test plugin for testing"""
        class TestPlugin(PatternPlugin):
            @property
            def info(self):
                return PluginInfo(
                    name="TestPlugin",
                    version="1.0.0",
                    description="Test plugin for testing"
                )
            
            def can_handle(self, pattern: str) -> bool:
                return "test" in pattern.lower()
            
            def expand(self, pattern: str, context: dict) -> dict:
                return {pattern.replace("*", "expanded"): context.get("value", 0)}
        
        return TestPlugin()

    def test_pattern_plugin_abstract(self):
        """Test that PatternPlugin cannot be instantiated directly"""
        with pytest.raises(TypeError):
            PatternPlugin()

    def test_pattern_plugin_concrete_implementation(self):
        """Test concrete implementation of PatternPlugin"""
        plugin = self.create_test_plugin()
        
        # Test info property
        info = plugin.info
        assert isinstance(info, PluginInfo)
        assert info.name == "TestPlugin"
        assert info.version == "1.0.0"
        assert info.description == "Test plugin for testing"
        
        # Test can_handle method
        assert plugin.can_handle("test_pattern") is True
        assert plugin.can_handle("other_pattern") is False
        
        # Test expand method
        context = {"value": 42}
        result = plugin.expand("test_*_pattern", context)
        assert result == {"test_expanded_pattern": 42}

    def test_pattern_plugin_methods_required(self):
        """Test that all abstract methods must be implemented"""
        # Missing info property
        class IncompletePlugin1(PatternPlugin):
            def can_handle(self, pattern: str) -> bool:
                return True
            
            def expand(self, pattern: str, context: dict) -> dict:
                return {}
        
        with pytest.raises(TypeError):
            IncompletePlugin1()
        
        # Missing can_handle method  
        class IncompletePlugin2(PatternPlugin):
            @property
            def info(self):
                return PluginInfo("test", "1.0", "test")
            
            def expand(self, pattern: str, context: dict) -> dict:
                return {}
        
        with pytest.raises(TypeError):
            IncompletePlugin2()
        
        # Missing expand method
        class IncompletePlugin3(PatternPlugin):
            @property
            def info(self):
                return PluginInfo("test", "1.0", "test")
            
            def can_handle(self, pattern: str) -> bool:
                return True
        
        with pytest.raises(TypeError):
            IncompletePlugin3()


class TestPluginManager:
    """Test PluginManager class"""

    def test_plugin_manager_init(self):
        """Test PluginManager initialization"""
        manager = PluginManager()
        assert manager.plugins == []

    def test_register_plugin(self):
        """Test registering a plugin"""
        manager = PluginManager()
        
        class TestPlugin(PatternPlugin):
            @property
            def info(self):
                return PluginInfo("TestPlugin", "1.0.0", "Test plugin")
            
            def can_handle(self, pattern: str) -> bool:
                return True
            
            def expand(self, pattern: str, context: dict) -> dict:
                return {}
        
        plugin = TestPlugin()
        
        with patch('strataregula.plugins.base.logger') as mock_logger:
            manager.register_plugin(plugin)
            
            assert plugin in manager.plugins
            assert len(manager.plugins) == 1
            mock_logger.info.assert_called_once_with("Registered plugin: TestPlugin")

    def test_unregister_plugin(self):
        """Test unregistering a plugin"""
        manager = PluginManager()
        
        class TestPlugin(PatternPlugin):
            @property
            def info(self):
                return PluginInfo("TestPlugin", "1.0.0", "Test plugin")
            
            def can_handle(self, pattern: str) -> bool:
                return True
            
            def expand(self, pattern: str, context: dict) -> dict:
                return {}
        
        plugin = TestPlugin()
        
        # Register first
        manager.register_plugin(plugin)
        assert plugin in manager.plugins
        
        # Then unregister
        with patch('strataregula.plugins.base.logger') as mock_logger:
            manager.unregister_plugin(plugin)
            
            assert plugin not in manager.plugins
            assert len(manager.plugins) == 0
            mock_logger.info.assert_called_once_with("Unregistered plugin: TestPlugin")

    def test_unregister_nonexistent_plugin(self):
        """Test unregistering a plugin that wasn't registered"""
        manager = PluginManager()
        
        class TestPlugin(PatternPlugin):
            @property
            def info(self):
                return PluginInfo("TestPlugin", "1.0.0", "Test plugin")
            
            def can_handle(self, pattern: str) -> bool:
                return True
            
            def expand(self, pattern: str, context: dict) -> dict:
                return {}
        
        plugin = TestPlugin()
        
        with patch('strataregula.plugins.base.logger') as mock_logger:
            manager.unregister_plugin(plugin)
            
            # Should not change anything
            assert len(manager.plugins) == 0
            # Logger should not be called for non-existent plugin
            mock_logger.info.assert_not_called()

    def test_get_plugin_for_pattern(self):
        """Test getting plugin for a specific pattern"""
        manager = PluginManager()
        
        class TestPlugin1(PatternPlugin):
            @property
            def info(self):
                return PluginInfo("TestPlugin1", "1.0.0", "Test plugin 1")
            
            def can_handle(self, pattern: str) -> bool:
                return "test1" in pattern
            
            def expand(self, pattern: str, context: dict) -> dict:
                return {}
        
        class TestPlugin2(PatternPlugin):
            @property
            def info(self):
                return PluginInfo("TestPlugin2", "1.0.0", "Test plugin 2")
            
            def can_handle(self, pattern: str) -> bool:
                return "test2" in pattern
            
            def expand(self, pattern: str, context: dict) -> dict:
                return {}
        
        plugin1 = TestPlugin1()
        plugin2 = TestPlugin2()
        
        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)
        
        # Test finding correct plugin
        found_plugin = manager.get_plugin_for_pattern("pattern_test1_here")
        assert found_plugin is plugin1
        
        found_plugin = manager.get_plugin_for_pattern("pattern_test2_here")
        assert found_plugin is plugin2
        
        # Test no matching plugin
        found_plugin = manager.get_plugin_for_pattern("no_match_pattern")
        assert found_plugin is None

    def test_get_plugin_for_pattern_first_match(self):
        """Test that first matching plugin is returned"""
        manager = PluginManager()
        
        class TestPlugin1(PatternPlugin):
            @property
            def info(self):
                return PluginInfo("TestPlugin1", "1.0.0", "Test plugin 1")
            
            def can_handle(self, pattern: str) -> bool:
                return "common" in pattern
            
            def expand(self, pattern: str, context: dict) -> dict:
                return {"plugin1": True}
        
        class TestPlugin2(PatternPlugin):
            @property
            def info(self):
                return PluginInfo("TestPlugin2", "1.0.0", "Test plugin 2")
            
            def can_handle(self, pattern: str) -> bool:
                return "common" in pattern
            
            def expand(self, pattern: str, context: dict) -> dict:
                return {"plugin2": True}
        
        plugin1 = TestPlugin1()
        plugin2 = TestPlugin2()
        
        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)
        
        # Should return first registered plugin
        found_plugin = manager.get_plugin_for_pattern("common_pattern")
        assert found_plugin is plugin1

    def test_expand_pattern_with_plugin(self):
        """Test expanding pattern using appropriate plugin"""
        manager = PluginManager()
        
        class TestPlugin(PatternPlugin):
            @property
            def info(self):
                return PluginInfo("TestPlugin", "1.0.0", "Test plugin")
            
            def can_handle(self, pattern: str) -> bool:
                return "expandable" in pattern
            
            def expand(self, pattern: str, context: dict) -> dict:
                return {pattern.replace("*", "processed"): context.get("value", 0) * 2}
        
        plugin = TestPlugin()
        manager.register_plugin(plugin)
        
        context = {"value": 21}
        result = manager.expand_pattern("expandable_*_pattern", context)
        
        assert result == {"expandable_processed_pattern": 42}

    def test_expand_pattern_without_plugin(self):
        """Test expanding pattern when no plugin can handle it"""
        manager = PluginManager()
        
        context = {"value": 42}
        result = manager.expand_pattern("unhandled_pattern", context)
        
        # Should return default expansion
        assert result == {"unhandled_pattern": 42}

    def test_expand_pattern_without_plugin_no_value(self):
        """Test expanding pattern when no plugin can handle it and no value in context"""
        manager = PluginManager()
        
        context = {}
        result = manager.expand_pattern("unhandled_pattern", context)
        
        # Should return default expansion with None value
        assert result == {"unhandled_pattern": None}

    def test_list_plugins(self):
        """Test listing all registered plugins"""
        manager = PluginManager()
        
        class TestPlugin1(PatternPlugin):
            @property
            def info(self):
                return PluginInfo("TestPlugin1", "1.0.0", "Test plugin 1")
            
            def can_handle(self, pattern: str) -> bool:
                return True
            
            def expand(self, pattern: str, context: dict) -> dict:
                return {}
        
        class TestPlugin2(PatternPlugin):
            @property
            def info(self):
                return PluginInfo("TestPlugin2", "2.0.0", "Test plugin 2")
            
            def can_handle(self, pattern: str) -> bool:
                return True
            
            def expand(self, pattern: str, context: dict) -> dict:
                return {}
        
        plugin1 = TestPlugin1()
        plugin2 = TestPlugin2()
        
        # Test empty list
        assert manager.list_plugins() == []
        
        # Test with plugins
        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)
        
        plugin_infos = manager.list_plugins()
        assert len(plugin_infos) == 2
        
        # Check that info objects are returned, not plugin objects
        assert all(isinstance(info, PluginInfo) for info in plugin_infos)
        
        # Check specific plugin info
        names = [info.name for info in plugin_infos]
        assert "TestPlugin1" in names
        assert "TestPlugin2" in names
        
        versions = [info.version for info in plugin_infos]
        assert "1.0.0" in versions
        assert "2.0.0" in versions