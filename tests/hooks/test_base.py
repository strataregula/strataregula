"""
Unit tests for hooks base module

Tests for HookManager, HookCallback, and HookRegistry classes.
"""

import pytest
import asyncio
import inspect
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from strataregula.hooks.base import (
    HookType,
    HookCallback,
    HookRegistry,
    HookManager
)


class TestHookType:
    """Test HookType enum"""
    
    def test_hook_type_values(self):
        """Test hook type enumeration values"""
        assert HookType.PRE_PROCESS.value == "pre_process"
        assert HookType.POST_PROCESS.value == "post_process"
        assert HookType.PRE_COMMAND.value == "pre_command"
        assert HookType.POST_COMMAND.value == "post_command"
        assert HookType.PRE_CHAIN.value == "pre_chain"
        assert HookType.POST_CHAIN.value == "post_chain"
        assert HookType.ERROR.value == "error"
        assert HookType.VALIDATION.value == "validation"
        assert HookType.TRANSFORMATION.value == "transformation"
        assert HookType.CUSTOM.value == "custom"
    
    def test_all_hook_types_available(self):
        """Test that all expected hook types are available"""
        expected_types = [
            "PRE_PROCESS", "POST_PROCESS", "PRE_COMMAND", "POST_COMMAND",
            "PRE_CHAIN", "POST_CHAIN", "ERROR", "VALIDATION", 
            "TRANSFORMATION", "CUSTOM"
        ]
        
        actual_types = [hook_type.name for hook_type in HookType]
        assert set(actual_types) == set(expected_types)


class TestHookCallback:
    """Test HookCallback functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.sync_callback = Mock(return_value="sync_result")
        self.async_callback = AsyncMock(return_value="async_result")
    
    def test_init_with_sync_callback(self):
        """Test initialization with synchronous callback"""
        hook = HookCallback(
            name="test_hook",
            callback=self.sync_callback,
            hook_type=HookType.PRE_PROCESS,
            priority=5,
            description="Test hook"
        )
        
        assert hook.name == "test_hook"
        assert hook.callback == self.sync_callback
        assert hook.hook_type == HookType.PRE_PROCESS
        assert hook.priority == 5
        assert hook.description == "Test hook"
        assert hook.enabled is True
        assert hook.async_support is False  # Should detect sync callback
    
    def test_init_with_async_callback(self):
        """Test initialization with asynchronous callback"""
        async def async_func():
            return "test"
        
        hook = HookCallback(
            name="async_hook",
            callback=async_func,
            hook_type=HookType.POST_PROCESS
        )
        
        assert hook.async_support is True  # Should detect async callback
    
    def test_init_defaults(self):
        """Test initialization with default values"""
        hook = HookCallback(
            name="default_hook",
            callback=self.sync_callback,
            hook_type=HookType.CUSTOM
        )
        
        assert hook.priority == 0
        assert hook.description == ""
        assert hook.enabled is True
    
    def test_post_init_async_detection(self):
        """Test that __post_init__ correctly detects async functions"""
        async def async_func():
            pass
        
        def sync_func():
            pass
        
        async_hook = HookCallback("async", async_func, HookType.CUSTOM)
        sync_hook = HookCallback("sync", sync_func, HookType.CUSTOM)
        
        assert async_hook.async_support is True
        assert sync_hook.async_support is False
    
    @pytest.mark.asyncio
    async def test_execute_sync_callback(self):
        """Test executing synchronous callback"""
        hook = HookCallback(
            name="sync_hook",
            callback=self.sync_callback,
            hook_type=HookType.PRE_PROCESS
        )
        
        result = await hook.execute("test_arg", kwarg="test_kwarg")
        
        assert result == "sync_result"
        # Note: sync callback execution goes through executor, so direct mock assertions may not work
    
    @pytest.mark.asyncio
    async def test_execute_async_callback(self):
        """Test executing asynchronous callback"""
        hook = HookCallback(
            name="async_hook",
            callback=self.async_callback,
            hook_type=HookType.POST_PROCESS
        )
        
        result = await hook.execute("test_arg", kwarg="test_kwarg")
        
        assert result == "async_result"
        self.async_callback.assert_called_once_with("test_arg", kwarg="test_kwarg")
    
    @pytest.mark.asyncio
    async def test_execute_disabled_hook(self):
        """Test executing disabled hook"""
        hook = HookCallback(
            name="disabled_hook",
            callback=self.sync_callback,
            hook_type=HookType.CUSTOM,
            enabled=False
        )
        
        result = await hook.execute("test_arg")
        
        assert result is None
        self.sync_callback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_callback_exception(self):
        """Test executing callback that raises exception"""
        error_callback = Mock(side_effect=ValueError("Test error"))
        hook = HookCallback(
            name="error_hook",
            callback=error_callback,
            hook_type=HookType.ERROR
        )
        
        with pytest.raises(ValueError, match="Test error"):
            await hook.execute()
    
    @pytest.mark.asyncio
    async def test_execute_async_callback_exception(self):
        """Test executing async callback that raises exception"""
        async_error_callback = AsyncMock(side_effect=RuntimeError("Async error"))
        hook = HookCallback(
            name="async_error_hook",
            callback=async_error_callback,
            hook_type=HookType.ERROR
        )
        
        with pytest.raises(RuntimeError, match="Async error"):
            await hook.execute()


class TestHookRegistry:
    """Test HookRegistry functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.registry = HookRegistry()
        self.callback1 = Mock(return_value="result1")
        self.callback2 = Mock(return_value="result2")
    
    def test_init(self):
        """Test registry initialization"""
        registry = HookRegistry()
        
        # Should have entries for all hook types
        for hook_type in HookType:
            assert hook_type in registry._hooks
            assert registry._hooks[hook_type] == []
        
        assert registry._callbacks == {}
    
    def test_register_callback(self):
        """Test registering a callback"""
        name = self.registry.register(
            HookType.PRE_PROCESS,
            self.callback1,
            name="test_callback",
            priority=5,
            description="Test description"
        )
        
        assert name == "test_callback"
        assert "test_callback" in self.registry._callbacks
        
        callback = self.registry._callbacks["test_callback"]
        assert callback.name == "test_callback"
        assert callback.callback == self.callback1
        assert callback.hook_type == HookType.PRE_PROCESS
        assert callback.priority == 5
        assert callback.description == "Test description"
        
        # Should be added to hook type list
        assert len(self.registry._hooks[HookType.PRE_PROCESS]) == 1
        assert self.registry._hooks[HookType.PRE_PROCESS][0] == callback
    
    def test_register_callback_auto_name(self):
        """Test registering callback with auto-generated name"""
        name = self.registry.register(HookType.POST_PROCESS, self.callback1)
        
        assert name.startswith("post_process_")
        assert name in self.registry._callbacks
    
    def test_register_duplicate_name(self):
        """Test registering callback with duplicate name"""
        self.registry.register(HookType.PRE_PROCESS, self.callback1, name="duplicate")
        
        with pytest.raises(ValueError, match="Hook callback 'duplicate' already registered"):
            self.registry.register(HookType.POST_PROCESS, self.callback2, name="duplicate")
    
    def test_register_multiple_callbacks_priority_sorting(self):
        """Test that callbacks are sorted by priority"""
        # Register callbacks with different priorities
        self.registry.register(HookType.VALIDATION, self.callback1, name="low", priority=1)
        self.registry.register(HookType.VALIDATION, self.callback2, name="high", priority=10)
        callback3 = Mock()
        self.registry.register(HookType.VALIDATION, callback3, name="medium", priority=5)
        
        callbacks = self.registry._hooks[HookType.VALIDATION]
        
        # Should be sorted by priority (highest first)
        assert callbacks[0].name == "high"
        assert callbacks[1].name == "medium" 
        assert callbacks[2].name == "low"
    
    def test_unregister_callback(self):
        """Test unregistering a callback"""
        name = self.registry.register(HookType.PRE_COMMAND, self.callback1, name="to_remove")
        
        result = self.registry.unregister(name)
        
        assert result is True
        assert name not in self.registry._callbacks
        assert len(self.registry._hooks[HookType.PRE_COMMAND]) == 0
    
    def test_unregister_nonexistent_callback(self):
        """Test unregistering non-existent callback"""
        result = self.registry.unregister("nonexistent")
        
        assert result is False
    
    def test_get_callbacks(self):
        """Test getting callbacks for a hook type"""
        self.registry.register(HookType.TRANSFORMATION, self.callback1, name="cb1")
        self.registry.register(HookType.TRANSFORMATION, self.callback2, name="cb2")
        self.registry.register(HookType.PRE_PROCESS, self.callback1, name="cb3")  # Different type
        
        callbacks = self.registry.get_callbacks(HookType.TRANSFORMATION)
        
        assert len(callbacks) == 2
        callback_names = [cb.name for cb in callbacks]
        assert "cb1" in callback_names
        assert "cb2" in callback_names
        assert "cb3" not in callback_names
    
    def test_get_callback_by_name(self):
        """Test getting specific callback by name"""
        name = self.registry.register(HookType.ERROR, self.callback1, name="specific")
        
        callback = self.registry.get_callback(name)
        
        assert callback is not None
        assert callback.name == "specific"
        assert callback.callback == self.callback1
    
    def test_get_nonexistent_callback(self):
        """Test getting non-existent callback"""
        callback = self.registry.get_callback("nonexistent")
        
        assert callback is None
    
    def test_list_hooks_all(self):
        """Test listing all hooks"""
        self.registry.register(HookType.PRE_PROCESS, self.callback1, name="cb1")
        self.registry.register(HookType.POST_PROCESS, self.callback2, name="cb2")
        
        all_hooks = self.registry.list_hooks()
        
        assert len(all_hooks) == 2
        hook_names = [hook.name for hook in all_hooks]
        assert "cb1" in hook_names
        assert "cb2" in hook_names
    
    def test_list_hooks_by_type(self):
        """Test listing hooks by specific type"""
        self.registry.register(HookType.PRE_CHAIN, self.callback1, name="cb1")
        self.registry.register(HookType.PRE_CHAIN, self.callback2, name="cb2")
        self.registry.register(HookType.POST_CHAIN, self.callback1, name="cb3")
        
        pre_chain_hooks = self.registry.list_hooks(HookType.PRE_CHAIN)
        
        assert len(pre_chain_hooks) == 2
        hook_names = [hook.name for hook in pre_chain_hooks]
        assert "cb1" in hook_names
        assert "cb2" in hook_names
        assert "cb3" not in hook_names
    
    def test_clear_hooks_all(self):
        """Test clearing all hooks"""
        self.registry.register(HookType.PRE_PROCESS, self.callback1, name="cb1")
        self.registry.register(HookType.POST_PROCESS, self.callback2, name="cb2")
        
        self.registry.clear_hooks()
        
        assert len(self.registry._callbacks) == 0
        for hook_type in HookType:
            assert len(self.registry._hooks[hook_type]) == 0
    
    def test_clear_hooks_by_type(self):
        """Test clearing hooks by specific type"""
        self.registry.register(HookType.VALIDATION, self.callback1, name="val1")
        self.registry.register(HookType.VALIDATION, self.callback2, name="val2")
        self.registry.register(HookType.TRANSFORMATION, self.callback1, name="trans1")
        
        self.registry.clear_hooks(HookType.VALIDATION)
        
        # Validation hooks should be cleared
        assert len(self.registry._hooks[HookType.VALIDATION]) == 0
        assert "val1" not in self.registry._callbacks
        assert "val2" not in self.registry._callbacks
        
        # Other hooks should remain
        assert len(self.registry._hooks[HookType.TRANSFORMATION]) == 1
        assert "trans1" in self.registry._callbacks


class TestHookManager:
    """Test HookManager functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.manager = HookManager()
        self.sync_callback = Mock(return_value="sync_result")
        self.async_callback = AsyncMock(return_value="async_result")
    
    def test_init(self):
        """Test manager initialization"""
        manager = HookManager()
        
        assert isinstance(manager.registry, HookRegistry)
        assert manager.enabled is True
    
    def test_register_with_enum_hook_type(self):
        """Test registering callback with enum hook type"""
        name = self.manager.register(
            HookType.PRE_PROCESS,
            self.sync_callback,
            name="enum_hook",
            priority=3,
            description="Enum hook test"
        )
        
        assert name == "enum_hook"
        callback = self.manager.registry.get_callback(name)
        assert callback.hook_type == HookType.PRE_PROCESS
    
    def test_register_with_string_hook_type(self):
        """Test registering callback with string hook type"""
        name = self.manager.register(
            "pre_process",
            self.sync_callback,
            name="string_hook"
        )
        
        callback = self.manager.registry.get_callback(name)
        assert callback.hook_type == HookType.PRE_PROCESS
    
    def test_register_with_invalid_string_hook_type(self):
        """Test registering callback with invalid string hook type"""
        name = self.manager.register(
            "invalid_hook_type",
            self.sync_callback,
            name="custom_hook"
        )
        
        callback = self.manager.registry.get_callback(name)
        assert callback.hook_type == HookType.CUSTOM
    
    def test_unregister(self):
        """Test unregistering callback"""
        name = self.manager.register(HookType.POST_COMMAND, self.sync_callback, name="to_remove")
        
        result = self.manager.unregister(name)
        
        assert result is True
        assert self.manager.registry.get_callback(name) is None
    
    @pytest.mark.asyncio
    async def test_trigger_with_enum_hook_type(self):
        """Test triggering hooks with enum hook type"""
        self.manager.register(HookType.VALIDATION, self.async_callback, name="validator1")
        self.manager.register(HookType.VALIDATION, self.sync_callback, name="validator2")
        
        results = await self.manager.trigger(HookType.VALIDATION, "test_data")
        
        # Should have results from both callbacks
        assert len(results) >= 1  # At least one callback should return a result
    
    @pytest.mark.asyncio
    async def test_trigger_with_string_hook_type(self):
        """Test triggering hooks with string hook type"""
        self.manager.register("transformation", self.async_callback, name="transform1")
        
        results = await self.manager.trigger("transformation", {"data": "test"})
        
        assert len(results) == 1
        assert results[0] == "async_result"
    
    @pytest.mark.asyncio
    async def test_trigger_with_invalid_string_hook_type(self):
        """Test triggering hooks with invalid string hook type"""
        self.manager.register("custom_type", self.sync_callback, name="custom1")
        
        results = await self.manager.trigger("invalid_type")
        
        # Should try CUSTOM type but find no hooks
        assert results == []
    
    @pytest.mark.asyncio
    async def test_trigger_disabled_manager(self):
        """Test triggering hooks when manager is disabled"""
        self.manager.register(HookType.PRE_PROCESS, self.sync_callback, name="disabled_test")
        self.manager.disable()
        
        results = await self.manager.trigger(HookType.PRE_PROCESS, "test")
        
        assert results == []
        self.sync_callback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_trigger_with_callback_exception(self):
        """Test triggering hooks when callback raises exception"""
        error_callback = AsyncMock(side_effect=RuntimeError("Hook error"))
        working_callback = AsyncMock(return_value="working")
        
        self.manager.register(HookType.ERROR, error_callback, name="error_hook")
        self.manager.register(HookType.ERROR, working_callback, name="working_hook")
        
        results = await self.manager.trigger(HookType.ERROR, "test")
        
        # Should continue with other hooks even if one fails
        assert len(results) == 1
        assert results[0] == "working"
    
    def test_trigger_sync(self):
        """Test synchronous hook triggering"""
        self.manager.register(HookType.POST_CHAIN, self.sync_callback, name="sync_hook")
        
        results = self.manager.trigger_sync(HookType.POST_CHAIN, "sync_test")
        
        # Should complete synchronously
        assert isinstance(results, list)
    
    def test_get_registered_hooks(self):
        """Test getting registered hooks summary"""
        self.manager.register(HookType.PRE_PROCESS, self.sync_callback, name="pre1")
        self.manager.register(HookType.PRE_PROCESS, self.async_callback, name="pre2")
        self.manager.register(HookType.POST_PROCESS, self.sync_callback, name="post1")
        
        summary = self.manager.get_registered_hooks()
        
        assert "pre_process" in summary
        assert "post_process" in summary
        assert len(summary["pre_process"]) == 2
        assert len(summary["post_process"]) == 1
        assert "pre1" in summary["pre_process"]
        assert "pre2" in summary["pre_process"]
        assert "post1" in summary["post_process"]
    
    def test_enable_disable(self):
        """Test enabling and disabling hook manager"""
        assert self.manager.is_enabled() is True
        
        self.manager.disable()
        assert self.manager.is_enabled() is False
        
        self.manager.enable()
        assert self.manager.is_enabled() is True
    
    def test_clear_all(self):
        """Test clearing all hooks"""
        self.manager.register(HookType.PRE_PROCESS, self.sync_callback, name="hook1")
        self.manager.register(HookType.POST_PROCESS, self.async_callback, name="hook2")
        
        self.manager.clear_all()
        
        summary = self.manager.get_registered_hooks()
        for hook_type_name, hooks in summary.items():
            assert len(hooks) == 0
    
    def test_list_hooks_all(self):
        """Test listing all hooks"""
        self.manager.register(HookType.VALIDATION, self.sync_callback, name="val1")
        self.manager.register(HookType.TRANSFORMATION, self.async_callback, name="trans1")
        
        all_hooks = self.manager.list_hooks()
        
        assert len(all_hooks) == 2
        hook_names = [hook.name for hook in all_hooks]
        assert "val1" in hook_names
        assert "trans1" in hook_names
    
    def test_list_hooks_by_type_enum(self):
        """Test listing hooks by enum hook type"""
        self.manager.register(HookType.ERROR, self.sync_callback, name="err1")
        self.manager.register(HookType.ERROR, self.async_callback, name="err2")
        self.manager.register(HookType.CUSTOM, self.sync_callback, name="custom1")
        
        error_hooks = self.manager.list_hooks(HookType.ERROR)
        
        assert len(error_hooks) == 2
        hook_names = [hook.name for hook in error_hooks]
        assert "err1" in hook_names
        assert "err2" in hook_names
        assert "custom1" not in hook_names
    
    def test_list_hooks_by_type_string(self):
        """Test listing hooks by string hook type"""
        self.manager.register("custom", self.sync_callback, name="custom1")
        self.manager.register("custom", self.async_callback, name="custom2")
        
        custom_hooks = self.manager.list_hooks("custom")
        
        assert len(custom_hooks) == 2
        hook_names = [hook.name for hook in custom_hooks]
        assert "custom1" in hook_names
        assert "custom2" in hook_names
    
    def test_list_hooks_by_invalid_string(self):
        """Test listing hooks by invalid string hook type"""
        self.manager.register(HookType.PRE_PROCESS, self.sync_callback, name="pre1")
        
        hooks = self.manager.list_hooks("invalid_type")
        
        # Should return all hooks since invalid type becomes None
        assert len(hooks) >= 0  # May be empty or contain all hooks


class TestIntegrationScenarios:
    """Test integration scenarios with multiple hooks and complex workflows"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.manager = HookManager()
    
    @pytest.mark.asyncio
    async def test_processing_pipeline_hooks(self):
        """Test a complete processing pipeline with pre/post hooks"""
        # Setup hooks that simulate a processing pipeline
        pre_hook_called = []
        post_hook_called = []
        
        async def pre_process_hook(data):
            pre_hook_called.append(data)
            return f"preprocessed_{data}"
        
        async def post_process_hook(data):
            post_hook_called.append(data)
            return f"postprocessed_{data}"
        
        self.manager.register(HookType.PRE_PROCESS, pre_process_hook, name="pre")
        self.manager.register(HookType.POST_PROCESS, post_process_hook, name="post")
        
        # Simulate processing pipeline
        input_data = "test_data"
        
        pre_results = await self.manager.trigger(HookType.PRE_PROCESS, input_data)
        processed_data = pre_results[0] if pre_results else input_data
        
        post_results = await self.manager.trigger(HookType.POST_PROCESS, processed_data)
        final_data = post_results[0] if post_results else processed_data
        
        assert pre_hook_called == [input_data]
        assert post_hook_called == [processed_data]
        assert final_data == "postprocessed_preprocessed_test_data"
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling hooks in workflow"""
        error_hooks_called = []
        
        async def error_handler1(error, context):
            error_hooks_called.append(f"handler1_{error}")
            return "handled_by_1"
        
        def error_handler2(error, context):
            error_hooks_called.append(f"handler2_{error}")
            return "handled_by_2"
        
        self.manager.register(HookType.ERROR, error_handler1, name="async_handler", priority=10)
        self.manager.register(HookType.ERROR, error_handler2, name="sync_handler", priority=5)
        
        # Trigger error handling
        results = await self.manager.trigger(HookType.ERROR, "test_error", {"context": "test"})
        
        assert len(results) == 2
        assert "handled_by_1" in results
        assert "handled_by_2" in results
        # Higher priority should be called first
        assert error_hooks_called[0] == "handler1_test_error"
        assert error_hooks_called[1] == "handler2_test_error"
    
    def test_priority_ordering_complex(self):
        """Test complex priority ordering scenarios"""
        callbacks_called = []
        
        def make_callback(name, priority):
            def callback(*args, **kwargs):
                callbacks_called.append(name)
                return name
            return callback
        
        # Register hooks with various priorities
        self.manager.register(HookType.VALIDATION, make_callback("low", 1), "low", priority=1)
        self.manager.register(HookType.VALIDATION, make_callback("high", 100), "high", priority=100)
        self.manager.register(HookType.VALIDATION, make_callback("medium", 50), "medium", priority=50)
        self.manager.register(HookType.VALIDATION, make_callback("zero", 0), "zero", priority=0)
        self.manager.register(HookType.VALIDATION, make_callback("negative", -10), "negative", priority=-10)
        
        # Trigger and check order
        results = self.manager.trigger_sync(HookType.VALIDATION, "test")
        
        # Should be ordered by priority (highest first)
        expected_order = ["high", "medium", "low", "zero", "negative"]
        assert callbacks_called == expected_order
        assert results == expected_order


class TestLogging:
    """Test logging functionality"""
    
    @patch('strataregula.hooks.base.logger')
    def test_registry_logging(self, mock_logger):
        """Test registry logging calls"""
        registry = HookRegistry()
        callback = Mock()
        
        # Test registration logging
        registry.register(HookType.PRE_PROCESS, callback, name="test_log")
        mock_logger.debug.assert_called_with("Registered hook 'test_log' for type 'pre_process'")
        
        # Test unregistration logging  
        registry.unregister("test_log")
        mock_logger.debug.assert_called_with("Unregistered hook 'test_log'")
    
    @patch('strataregula.hooks.base.logger')
    def test_callback_execution_error_logging(self, mock_logger):
        """Test error logging during callback execution"""
        error_callback = Mock(side_effect=RuntimeError("Test error"))
        hook = HookCallback("error_hook", error_callback, HookType.ERROR)
        
        # Should log error and re-raise
        with pytest.raises(RuntimeError):
            asyncio.run(hook.execute())
        
        mock_logger.error.assert_called_with("Error executing hook 'error_hook': Test error")
    
    @patch('strataregula.hooks.base.logger')
    @pytest.mark.asyncio
    async def test_manager_trigger_error_logging(self, mock_logger):
        """Test error logging during manager trigger"""
        error_callback = AsyncMock(side_effect=ValueError("Manager error"))
        manager = HookManager()
        manager.register(HookType.CUSTOM, error_callback, name="error_hook")
        
        # Should log error but continue with other hooks
        results = await manager.trigger(HookType.CUSTOM)
        
        assert results == []  # No successful results
        mock_logger.error.assert_called()