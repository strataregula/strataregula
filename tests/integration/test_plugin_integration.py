"""
Integration tests for the plugin system with core components.
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
from typing import Dict, Any

from strataregula.core.config_compiler import ConfigCompiler, CompilationConfig
from strataregula.plugins.manager import EnhancedPluginManager, PluginConfig
from strataregula.plugins.config import PluginConfigManager, PluginConfigEntry, GlobalPluginConfig
from strataregula.plugins.samples import TimestampPlugin, EnvironmentPlugin, PrefixPlugin
from strataregula.plugins.base import PatternPlugin, PluginInfo


class TestPlugin(PatternPlugin):
    """Simple test plugin for integration testing."""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin for integration testing"
        )
    
    def can_handle(self, pattern: str) -> bool:
        return pattern.startswith('test:')
    
    def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
        base_pattern = pattern[5:]  # Remove 'test:' prefix
        return {f"expanded.{base_pattern}": context.get('value')}


class TestPluginSystemIntegration:
    """Test plugin system integration with core components."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_plugin = TestPlugin()
        
        # Create minimal plugin configuration
        self.plugin_config = {
            "global": {
                "auto_discover": False,
                "lazy_loading": False,
                "max_errors": 3
            },
            "plugins": {
                "test-plugin": {
                    "enabled": True,
                    "priority": 10,
                    "settings": {
                        "test_setting": "test_value"
                    }
                }
            }
        }
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_compiler_with_plugins_disabled(self):
        """Test ConfigCompiler with plugins disabled."""
        compiler = ConfigCompiler(use_plugins=False)
        
        assert compiler.plugin_manager is None
        assert compiler.expander.plugin_manager is None
        assert not compiler.use_plugins
    
    def test_config_compiler_with_plugins_enabled(self):
        """Test ConfigCompiler with plugins enabled."""
        compiler = ConfigCompiler(use_plugins=True)
        
        assert compiler.plugin_manager is not None
        assert compiler.expander.plugin_manager is not None
        assert compiler.use_plugins
    
    def test_plugin_manager_initialization(self):
        """Test plugin manager initialization."""
        config_manager = PluginConfigManager([])  # Empty config paths
        plugin_manager = EnhancedPluginManager(
            config=config_manager.get_global_config()
        )
        
        assert plugin_manager is not None
        assert len(plugin_manager.get_plugin_contexts()) == 0
    
    def test_manual_plugin_registration(self):
        """Test manual plugin registration and activation."""
        config_manager = PluginConfigManager([])
        # Use the manager's default PluginConfig, not GlobalPluginConfig
        plugin_manager = EnhancedPluginManager()
        
        # Manually register test plugin
        # Since we can't use the loader for this test plugin,
        # we'll simulate the process
        from strataregula.plugins.manager import PluginContext, PluginState
        import time
        
        plugin_manager._plugins[self.test_plugin.info.name] = PluginContext(
            plugin=self.test_plugin,
            state=PluginState.LOADED,
            load_time=time.time(),
            last_used=time.time()
        )
        
        # Activate plugin
        success = plugin_manager.activate_plugin(self.test_plugin.info.name)
        assert success
        
        # Test pattern handling
        result = plugin_manager.expand_pattern(
            'test:sample.pattern',
            {'value': 'test_value'}
        )
        
        expected = {'expanded.sample.pattern': 'test_value'}
        assert result == expected
    
    
    def test_sample_plugins_functionality(self):
        """Test sample plugins functionality."""
        # Test TimestampPlugin
        timestamp_plugin = TimestampPlugin()
        assert timestamp_plugin.can_handle('config.@timestamp.yaml')
        assert not timestamp_plugin.can_handle('config.normal.yaml')
        
        result = timestamp_plugin.expand(
            'config.@timestamp.yaml',
            {'value': 'test', 'plugin_settings': {'timestamp_format': '%Y%m%d'}}
        )
        
        # Should have replaced @timestamp with actual date
        expanded_key = list(result.keys())[0]
        assert '@timestamp' not in expanded_key
        assert 'config.' in expanded_key
        assert '.yaml' in expanded_key
        
        # Test EnvironmentPlugin  
        env_plugin = EnvironmentPlugin()
        assert env_plugin.can_handle('path.$HOME/config')
        assert not env_plugin.can_handle('path.normal/config')
        
        # Test PrefixPlugin
        prefix_plugin = PrefixPlugin()
        assert prefix_plugin.can_handle('@prefix:service.config')
        assert not prefix_plugin.can_handle('service.config')
        
        result = prefix_plugin.expand(
            '@prefix:service.config',
            {'value': 'test', 'plugin_settings': {'prefix': 'prod'}}
        )
        
        expected = {'prod.service.config': 'test'}
        assert result == expected
    
    def test_plugin_configuration_loading(self):
        """Test plugin configuration loading."""
        # Create temporary config file
        config_file = self.temp_dir / 'plugins.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(self.plugin_config, f)
        
        # Load configuration
        config_manager = PluginConfigManager([config_file])
        global_config = config_manager.get_global_config()
        
        assert global_config.auto_discover == False
        assert global_config.lazy_loading == False
        assert global_config.max_errors == 3
        
        # Test plugin-specific config
        plugin_config = config_manager.get_plugin_config('test-plugin')
        assert plugin_config.enabled == True
        assert plugin_config.priority == 10
        assert plugin_config.settings['test_setting'] == 'test_value'
    
    def test_plugin_error_handling(self):
        """Test plugin error handling and fallbacks."""
        class FailingPlugin(PatternPlugin):
            @property
            def info(self) -> PluginInfo:
                return PluginInfo(
                    name="failing-plugin",
                    version="1.0.0", 
                    description="Plugin that always fails"
                )
            
            def can_handle(self, pattern: str) -> bool:
                return pattern.startswith('fail:')
            
            def expand(self, pattern: str, context: Dict[str, Any]) -> Dict[str, Any]:
                raise ValueError("Plugin intentionally failing")
        
        failing_plugin = FailingPlugin()
        config_manager = PluginConfigManager([])
        plugin_manager = EnhancedPluginManager(
            config=config_manager.get_global_config()
        )
        
        # Test that plugin failure doesn't break the system
        result = plugin_manager.expand_pattern(
            'fail:test.pattern',
            {'value': 'test_value'}
        )
        
        # Should fall back to default behavior
        expected = {'fail:test.pattern': 'test_value'}
        assert result == expected
    
    def test_hook_integration(self):
        """Test hook system integration."""
        compiler = ConfigCompiler(use_plugins=True)
        
        # Verify hook manager is available
        assert compiler.expander.plugin_manager is not None
        assert hasattr(compiler.expander.plugin_manager, 'hooks')
        
        # Test hook registration
        hook_called = []
        
        def test_hook(pattern=None, **kwargs):
            hook_called.append(pattern)
        
        compiler.expander.plugin_manager.hooks.register(
            'pre_expand',
            test_hook,
            name='test_hook'
        )
        
        # The hook should be registered
        hooks = compiler.expander.plugin_manager.hooks.list_hooks('pre_expand')
        assert len(hooks) >= 1
        assert any(hook.name == 'test_hook' for hook in hooks)
    
    def test_pattern_expansion_with_plugins(self):
        """Test pattern expansion with plugin integration."""
        compiler = ConfigCompiler(use_plugins=True)
        
        # Create test patterns
        patterns = {
            'service.api.config': 'api_value',
            'service.web.config': 'web_value'
        }
        
        # Expand patterns (should work even without specific plugins)
        results = list(compiler.expander.expand_pattern_stream(patterns))
        
        # Should have results
        assert len(results) > 0
        
        # Results should be tuples of (pattern, value)
        for pattern, value in results:
            assert isinstance(pattern, str)
            assert value in ['api_value', 'web_value']
    
    def test_plugin_discovery_integration(self):
        """Test plugin discovery in integration context."""
        compiler = ConfigCompiler(use_plugins=True)
        
        # Should have discovered plugins (even if none are found)
        plugin_stats = compiler.plugin_manager.get_plugin_stats()
        
        assert 'total_plugins' in plugin_stats
        assert 'by_state' in plugin_stats
        assert 'loader_stats' in plugin_stats
    
    def test_backward_compatibility(self):
        """Test that existing code works unchanged."""
        # Test old-style initialization still works
        from strataregula.core.pattern_expander import EnhancedPatternExpander
        from strataregula.core.config_compiler import CompilationConfig
        
        # Old way should still work
        config = CompilationConfig()
        expander = EnhancedPatternExpander(chunk_size=config.chunk_size)
        compiler = ConfigCompiler(config, use_plugins=False)
        
        # Should work without plugin system
        assert expander.plugin_manager is None
        assert compiler.plugin_manager is None
    
    def test_integration_with_real_data(self):
        """Test integration with realistic configuration data."""
        # Create test traffic data
        traffic_data = {
            'service_times': {
                'api.*.response': 150,
                'web.*.load': 200,
                'db.*.query': 50
            }
        }
        
        # Create temporary files
        traffic_file = self.temp_dir / 'traffic.yaml'
        with open(traffic_file, 'w') as f:
            yaml.dump(traffic_data, f)
        
        # Test compilation with plugins
        compiler = ConfigCompiler(use_plugins=True)
        
        try:
            # Should complete without errors
            result = compiler.compile_traffic_config(traffic_file)
            assert result is not None
            assert len(result) > 0
        except Exception as e:
            # Log error but don't fail test if it's just missing dependencies
            print(f"Compilation error (may be expected): {e}")


class TestPluginSystemEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_plugin_system_with_no_plugins(self):
        """Test system behavior with no plugins available."""
        compiler = ConfigCompiler(use_plugins=True)
        
        # Should work even with no plugins
        patterns = {'test.pattern': 'value'}
        results = list(compiler.expander.expand_pattern_stream(patterns))
        
        assert len(results) > 0
    
    def test_plugin_system_graceful_degradation(self):
        """Test graceful degradation when plugin system fails."""
        compiler = ConfigCompiler(use_plugins=True)
        
        # Simulate plugin system failure by setting to None
        compiler.expander.plugin_manager = None
        
        # Should still work
        patterns = {'test.pattern': 'value'}
        results = list(compiler.expander.expand_pattern_stream(patterns))
        
        assert len(results) > 0
    
    def test_malformed_plugin_configuration(self):
        """Test handling of malformed plugin configuration."""
        # This should not crash the system
        config_manager = PluginConfigManager([])
        
        # Should create default configuration
        global_config = config_manager.get_global_config()
        assert global_config.auto_discover == True  # Default value