"""
Tests for pipe chain module
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock

from strataregula.pipe.chain import ChainContext, CommandChain, ChainExecutor


class TestChainContext:
    """Test ChainContext dataclass"""

    def test_context_creation(self):
        """Test creating ChainContext with all parameters"""
        data = {"test": "data"}
        metadata = {"meta": "info"}
        environment = {"ENV": "value"}
        hooks = Mock()
        container = Mock()
        
        context = ChainContext(
            data=data,
            metadata=metadata,
            environment=environment,
            hooks=hooks,
            container=container
        )
        
        assert context.data == data
        assert context.metadata == metadata
        assert context.environment == environment
        assert context.hooks == hooks
        assert context.container == container

    def test_context_creation_with_defaults(self):
        """Test creating ChainContext with default values"""
        with patch('strataregula.pipe.chain.HookManager') as mock_hook, \
             patch('strataregula.pipe.chain.Container') as mock_container:
            
            context = ChainContext(
                data={"test": "data"},
                metadata=None,
                environment=None,
                hooks=None,
                container=None
            )
            
            assert context.data == {"test": "data"}
            assert context.metadata == {}
            assert context.environment == {}
            mock_hook.assert_called_once()
            mock_container.assert_called_once()


class TestCommandChain:
    """Test CommandChain class"""

    def test_chain_init(self):
        """Test CommandChain initialization"""
        chain = CommandChain("test_chain")
        assert chain.name == "test_chain"
        assert chain.commands == []
        assert hasattr(chain, 'hooks')
        assert hasattr(chain, 'container')

    def test_chain_init_default_name(self):
        """Test CommandChain initialization with default name"""
        chain = CommandChain()
        assert chain.name == "default"

    def test_add_command_basic(self):
        """Test adding a basic command"""
        chain = CommandChain("test")
        
        result = chain.add_command("test_command")
        
        # Should return self for chaining
        assert result is chain
        
        # Command should be added with defaults
        assert len(chain.commands) == 1
        cmd = chain.commands[0]
        assert cmd['command'] == "test_command"
        assert cmd['args'] == []
        assert cmd['kwargs'] == {}
        assert cmd['condition'] is None
        assert cmd['error_handling'] == 'continue'

    def test_add_command_with_parameters(self):
        """Test adding a command with all parameters"""
        chain = CommandChain("test")
        
        chain.add_command(
            "test_command",
            args=["arg1", "arg2"],
            kwargs={"param": "value"},
            condition="data is not None",
            error_handling="stop"
        )
        
        assert len(chain.commands) == 1
        cmd = chain.commands[0]
        assert cmd['command'] == "test_command"
        assert cmd['args'] == ["arg1", "arg2"]
        assert cmd['kwargs'] == {"param": "value"}
        assert cmd['condition'] == "data is not None"
        assert cmd['error_handling'] == "stop"

    def test_add_multiple_commands(self):
        """Test adding multiple commands"""
        chain = CommandChain("test")
        
        chain.add_command("cmd1").add_command("cmd2").add_command("cmd3")
        
        assert len(chain.commands) == 3
        assert chain.commands[0]['command'] == "cmd1"
        assert chain.commands[1]['command'] == "cmd2"
        assert chain.commands[2]['command'] == "cmd3"

    def test_add_hook(self):
        """Test adding a hook to the chain"""
        chain = CommandChain("test")
        callback = Mock()
        
        result = chain.add_hook("test_hook", callback)
        
        # Should return self for chaining
        assert result is chain
        
        # Hook should be registered
        chain.hooks.register.assert_called_once_with("test_hook", callback)

    def test_validate_empty_chain(self):
        """Test validation of empty chain"""
        chain = CommandChain("test")
        assert chain.validate() is False

    def test_validate_non_empty_chain(self):
        """Test validation of chain with commands"""
        chain = CommandChain("test")
        chain.add_command("test_command")
        assert chain.validate() is True


class TestChainExecutor:
    """Test ChainExecutor class"""

    def test_executor_init(self):
        """Test ChainExecutor initialization"""
        with patch('strataregula.pipe.chain.CommandRegistry') as mock_registry:
            executor = ChainExecutor()
            assert hasattr(executor, 'registry')
            assert hasattr(executor, 'hooks')
            mock_registry.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_invalid_chain(self):
        """Test executing an invalid chain"""
        with patch('strataregula.pipe.chain.CommandRegistry'):
            executor = ChainExecutor()
            empty_chain = CommandChain("empty")
            
            with pytest.raises(ValueError, match="Invalid command chain"):
                await executor.execute_chain(empty_chain)

    @pytest.mark.asyncio
    async def test_execute_chain_with_context(self):
        """Test executing chain with provided context"""
        with patch('strataregula.pipe.chain.CommandRegistry') as mock_registry:
            # Setup mocks
            mock_command = Mock()
            mock_command.execute = AsyncMock(return_value={"result": "processed"})
            
            mock_registry_instance = Mock()
            mock_registry_instance.get_command.return_value = mock_command
            mock_registry.return_value = mock_registry_instance
            
            executor = ChainExecutor()
            
            # Create test chain and context
            chain = CommandChain("test")
            chain.add_command("test_cmd")
            
            context = ChainContext(
                data={"input": "data"},
                metadata={},
                environment={},
                hooks=Mock(),
                container=Mock()
            )
            
            # Mock hooks
            executor.hooks = Mock()
            executor.hooks.trigger = AsyncMock()
            chain.hooks = Mock()
            chain.hooks.trigger = AsyncMock()
            
            result = await executor.execute_chain(chain, {"input": "data"}, context)
            
            # Verify command was executed
            mock_command.execute.assert_called_once()
            assert result == {"result": "processed"}

    @pytest.mark.asyncio
    async def test_execute_chain_without_context(self):
        """Test executing chain without provided context"""
        with patch('strataregula.pipe.chain.CommandRegistry') as mock_registry, \
             patch.dict(os.environ, {"TEST_ENV": "value"}):
            
            # Setup mocks
            mock_command = Mock()
            mock_command.execute = AsyncMock(return_value={"result": "processed"})
            
            mock_registry_instance = Mock()
            mock_registry_instance.get_command.return_value = mock_command
            mock_registry.return_value = mock_registry_instance
            
            executor = ChainExecutor()
            
            # Create test chain
            chain = CommandChain("test")
            chain.add_command("test_cmd")
            
            # Mock hooks
            executor.hooks = Mock()
            executor.hooks.trigger = AsyncMock()
            chain.hooks = Mock()
            chain.hooks.trigger = AsyncMock()
            
            result = await executor.execute_chain(chain, {"input": "data"})
            
            # Verify command was executed
            mock_command.execute.assert_called_once()
            assert result == {"result": "processed"}

    @pytest.mark.asyncio
    async def test_execute_unknown_command(self):
        """Test executing chain with unknown command"""
        with patch('strataregula.pipe.chain.CommandRegistry') as mock_registry:
            mock_registry_instance = Mock()
            mock_registry_instance.get_command.return_value = None
            mock_registry.return_value = mock_registry_instance
            
            executor = ChainExecutor()
            
            chain = CommandChain("test")
            chain.add_command("unknown_cmd")
            
            # Mock hooks
            executor.hooks = Mock()
            executor.hooks.trigger = AsyncMock()
            chain.hooks = Mock()
            chain.hooks.trigger = AsyncMock()
            
            with pytest.raises(ValueError, match="Unknown command"):
                await executor.execute_chain(chain, {"input": "data"})

    @pytest.mark.asyncio
    async def test_execute_with_condition_true(self):
        """Test executing command with condition that evaluates to True"""
        with patch('strataregula.pipe.chain.CommandRegistry') as mock_registry:
            # Setup mocks
            mock_command = Mock()
            mock_command.execute = AsyncMock(return_value={"result": "processed"})
            
            mock_registry_instance = Mock()
            mock_registry_instance.get_command.return_value = mock_command
            mock_registry.return_value = mock_registry_instance
            
            executor = ChainExecutor()
            
            chain = CommandChain("test")
            chain.add_command("test_cmd", condition="data is not None")
            
            # Mock hooks
            executor.hooks = Mock()
            executor.hooks.trigger = AsyncMock()
            chain.hooks = Mock()
            chain.hooks.trigger = AsyncMock()
            
            result = await executor.execute_chain(chain, {"input": "data"})
            
            # Command should be executed since condition is True
            mock_command.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_condition_false(self):
        """Test executing command with condition that evaluates to False"""
        with patch('strataregula.pipe.chain.CommandRegistry') as mock_registry:
            mock_registry_instance = Mock()
            mock_registry_instance.get_command.return_value = Mock()
            mock_registry.return_value = mock_registry_instance
            
            executor = ChainExecutor()
            
            chain = CommandChain("test")
            chain.add_command("test_cmd", condition="data is None")  # Will be False
            
            # Mock hooks
            executor.hooks = Mock()
            executor.hooks.trigger = AsyncMock()
            chain.hooks = Mock()
            chain.hooks.trigger = AsyncMock()
            
            result = await executor.execute_chain(chain, {"input": "data"})
            
            # Command should not be executed since condition is False
            mock_registry_instance.get_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_with_error_continue(self):
        """Test executing chain with error handling set to 'continue'"""
        with patch('strataregula.pipe.chain.CommandRegistry') as mock_registry:
            # Setup mocks - first command fails, second succeeds
            mock_command1 = Mock()
            mock_command1.execute = AsyncMock(side_effect=Exception("Command failed"))
            
            mock_command2 = Mock()
            mock_command2.execute = AsyncMock(return_value={"result": "success"})
            
            mock_registry_instance = Mock()
            mock_registry_instance.get_command.side_effect = [mock_command1, mock_command2]
            mock_registry.return_value = mock_registry_instance
            
            executor = ChainExecutor()
            
            chain = CommandChain("test")
            chain.add_command("failing_cmd", error_handling="continue")
            chain.add_command("success_cmd")
            
            # Mock hooks
            executor.hooks = Mock()
            executor.hooks.trigger = AsyncMock()
            chain.hooks = Mock()
            chain.hooks.trigger = AsyncMock()
            
            result = await executor.execute_chain(chain, {"input": "data"})
            
            # Should continue to second command despite first failing
            assert mock_command1.execute.call_count == 1
            assert mock_command2.execute.call_count == 1
            executor.hooks.trigger.assert_any_call('command_error', unittest.mock.ANY, 'failing_cmd', unittest.mock.ANY, 0)

    @pytest.mark.asyncio
    async def test_execute_with_error_stop(self):
        """Test executing chain with error handling set to 'stop'"""
        with patch('strataregula.pipe.chain.CommandRegistry') as mock_registry:
            mock_command = Mock()
            mock_command.execute = AsyncMock(side_effect=Exception("Command failed"))
            
            mock_registry_instance = Mock()
            mock_registry_instance.get_command.return_value = mock_command
            mock_registry.return_value = mock_registry_instance
            
            executor = ChainExecutor()
            
            chain = CommandChain("test")
            chain.add_command("failing_cmd", error_handling="stop")
            
            # Mock hooks
            executor.hooks = Mock()
            executor.hooks.trigger = AsyncMock()
            chain.hooks = Mock()
            chain.hooks.trigger = AsyncMock()
            
            with pytest.raises(Exception, match="Command failed"):
                await executor.execute_chain(chain, {"input": "data"})

    def test_execute_chain_sync(self):
        """Test synchronous chain execution"""
        with patch('strataregula.pipe.chain.CommandRegistry'):
            executor = ChainExecutor()
            chain = CommandChain("test")
            chain.add_command("test_cmd")
            
            with patch.object(executor, 'execute_chain', return_value=asyncio.Future()) as mock_execute:
                mock_execute.return_value.set_result({"sync": "result"})
                
                result = executor.execute_chain_sync(chain, {"input": "data"})
                assert result == {"sync": "result"}

    def test_evaluate_condition_true(self):
        """Test condition evaluation that returns True"""
        with patch('strataregula.pipe.chain.CommandRegistry'):
            executor = ChainExecutor()
            context = ChainContext(
                data={"value": 10},
                metadata={"meta": "test"},
                environment={"ENV": "production"},
                hooks=Mock(),
                container=Mock()
            )
            
            # Test simple condition
            result = executor._evaluate_condition("data['value'] > 5", context)
            assert result is True

    def test_evaluate_condition_false(self):
        """Test condition evaluation that returns False"""
        with patch('strataregula.pipe.chain.CommandRegistry'):
            executor = ChainExecutor()
            context = ChainContext(
                data={"value": 3},
                metadata={},
                environment={},
                hooks=Mock(),
                container=Mock()
            )
            
            # Test condition that evaluates to False
            result = executor._evaluate_condition("data['value'] > 5", context)
            assert result is False

    def test_evaluate_condition_error(self):
        """Test condition evaluation with syntax error"""
        with patch('strataregula.pipe.chain.CommandRegistry'):
            executor = ChainExecutor()
            context = ChainContext(
                data={},
                metadata={},
                environment={},
                hooks=Mock(),
                container=Mock()
            )
            
            # Test invalid condition
            result = executor._evaluate_condition("invalid syntax]", context)
            assert result is False

    @pytest.mark.asyncio
    async def test_hooks_execution_order(self):
        """Test that hooks are executed in the correct order"""
        with patch('strataregula.pipe.chain.CommandRegistry') as mock_registry:
            mock_command = Mock()
            mock_command.execute = AsyncMock(return_value={"result": "success"})
            
            mock_registry_instance = Mock()
            mock_registry_instance.get_command.return_value = mock_command
            mock_registry.return_value = mock_registry_instance
            
            executor = ChainExecutor()
            chain = CommandChain("test")
            chain.add_command("test_cmd")
            
            # Mock hooks
            executor.hooks = Mock()
            executor.hooks.trigger = AsyncMock()
            chain.hooks = Mock()
            chain.hooks.trigger = AsyncMock()
            
            await executor.execute_chain(chain, {"input": "data"})
            
            # Verify hook execution order
            executor_calls = [call[0][0] for call in executor.hooks.trigger.call_args_list]
            chain_calls = [call[0][0] for call in chain.hooks.trigger.call_args_list]
            
            assert 'pre_chain' in executor_calls
            assert 'pre_command' in executor_calls
            assert 'post_command' in executor_calls
            assert 'post_chain' in executor_calls
            
            assert 'pre_chain' in chain_calls
            assert 'pre_command' in chain_calls
            assert 'post_command' in chain_calls
            assert 'post_chain' in chain_calls