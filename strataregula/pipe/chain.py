"""
Command Chain - Core functionality for chaining commands in PiPE system.
"""

import sys
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from pathlib import Path
import yaml

from ..hooks.base import HookManager
from ..di.container import Container


@dataclass
class ChainContext:
    """Context passed between commands in a chain."""
    data: Any
    metadata: Dict[str, Any]
    environment: Dict[str, str]
    hooks: HookManager
    container: Container
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.environment is None:
            self.environment = {}
        if self.hooks is None:
            self.hooks = HookManager()
        if self.container is None:
            self.container = Container()


class CommandChain:
    """Represents a chain of commands to be executed sequentially."""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.commands: List[Dict[str, Any]] = []
        self.hooks = HookManager()
        self.container = Container()
        
    def add_command(self, command: str, **kwargs) -> 'CommandChain':
        """Add a command to the chain."""
        self.commands.append({
            'command': command,
            'args': kwargs.get('args', []),
            'kwargs': kwargs.get('kwargs', {}),
            'condition': kwargs.get('condition'),
            'error_handling': kwargs.get('error_handling', 'continue')
        })
        return self
    
    def add_hook(self, hook_type: str, callback: Callable) -> 'CommandChain':
        """Add a hook to the chain."""
        self.hooks.register(hook_type, callback)
        return self
    
    def validate(self) -> bool:
        """Validate the command chain configuration."""
        return len(self.commands) > 0


class ChainExecutor:
    """Executes command chains with support for hooks and error handling."""
    
    def __init__(self):
        self.registry = CommandRegistry()
        self.hooks = HookManager()
        
    async def execute_chain(self, chain: CommandChain, 
                           initial_data: Any = None,
                           context: Optional[ChainContext] = None) -> Any:
        """Execute a command chain asynchronously."""
        if not chain.validate():
            raise ValueError("Invalid command chain")
            
        if context is None:
            context = ChainContext(
                data=initial_data,
                metadata={},
                environment=dict(sys.environ),
                hooks=chain.hooks,
                container=chain.container
            )
        
        # Execute pre-chain hooks
        await self.hooks.trigger('pre_chain', context)
        await chain.hooks.trigger('pre_chain', context)
        
        result = initial_data
        
        try:
            for i, cmd_config in enumerate(chain.commands):
                command_name = cmd_config['command']
                args = cmd_config['args']
                kwargs = cmd_config['kwargs']
                condition = cmd_config['condition']
                error_handling = cmd_config['error_handling']
                
                # Check condition
                if condition and not self._evaluate_condition(condition, context):
                    continue
                
                # Execute pre-command hooks
                await self.hooks.trigger('pre_command', context, command_name, i)
                await chain.hooks.trigger('pre_command', context, command_name, i)
                
                try:
                    # Execute command
                    command = self.registry.get_command(command_name)
                    if command:
                        result = await command.execute(result, *args, **kwargs, context=context)
                        context.data = result
                    else:
                        raise ValueError(f"Unknown command: {command_name}")
                        
                except Exception as e:
                    if error_handling == 'stop':
                        raise
                    elif error_handling == 'continue':
                        await self.hooks.trigger('command_error', context, command_name, e, i)
                        continue
                    elif error_handling == 'retry':
                        # Implement retry logic
                        pass
                
                # Execute post-command hooks
                await self.hooks.trigger('post_command', context, command_name, i, result)
                await chain.hooks.trigger('post_command', context, command_name, i, result)
                
        except Exception as e:
            await self.hooks.trigger('chain_error', context, e)
            await chain.hooks.trigger('chain_error', context, e)
            raise
            
        # Execute post-chain hooks
        await self.hooks.trigger('post_chain', context, result)
        await chain.hooks.trigger('post_chain', context, result)
        
        return result
    
    def execute_chain_sync(self, chain: CommandChain, 
                          initial_data: Any = None,
                          context: Optional[ChainContext] = None) -> Any:
        """Execute a command chain synchronously."""
        return asyncio.run(self.execute_chain(chain, initial_data, context))
    
    def _evaluate_condition(self, condition: str, context: ChainContext) -> bool:
        """Evaluate a condition string against the context."""
        try:
            # Simple condition evaluation - can be extended
            return eval(condition, {"__builtins__": {}}, {
                'data': context.data,
                'metadata': context.metadata,
                'env': context.environment
            })
        except:
            return False
