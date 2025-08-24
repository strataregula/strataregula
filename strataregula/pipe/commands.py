"""
Command System - Base classes and registry for PiPE commands.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable, Type
from dataclasses import dataclass
import inspect

from ..hooks.base import HookManager


@dataclass
class CommandInfo:
    """Information about a registered command."""
    name: str
    description: str
    version: str
    author: str
    category: str
    async_support: bool
    input_types: List[str]
    output_types: List[str]
    examples: List[str]


class BaseCommand(ABC):
    """Base class for all PiPE commands."""
    
    def __init__(self):
        self.name = self.__class__.__name__.lower()
        self.description = getattr(self, '__doc__', 'No description available')
        self.version = getattr(self, 'version', '1.0.0')
        self.author = getattr(self, 'author', 'Unknown')
        self.category = getattr(self, 'category', 'general')
        self.input_types = getattr(self, 'input_types', ['any'])
        self.output_types = getattr(self, 'output_types', ['any'])
        self.examples = getattr(self, 'examples', [])
        self.hooks = HookManager()
        
    @abstractmethod
    async def execute(self, data: Any, *args, **kwargs) -> Any:
        """Execute the command. Must be implemented by subclasses."""
        pass
    
    def execute_sync(self, data: Any, *args, **kwargs) -> Any:
        """Execute the command synchronously."""
        return asyncio.run(self.execute(data, *args, **kwargs))
    
    def validate_input(self, data: Any) -> bool:
        """Validate input data type."""
        if 'any' in self.input_types:
            return True
        
        data_type = type(data).__name__.lower()
        return data_type in self.input_types
    
    def get_info(self) -> CommandInfo:
        """Get command information."""
        return CommandInfo(
            name=self.name,
            description=self.description,
            version=self.version,
            author=self.author,
            category=self.category,
            async_support=inspect.iscoroutinefunction(self.execute),
            input_types=self.input_types,
            output_types=self.output_types,
            examples=self.examples
        )


class CommandRegistry:
    """Registry for managing PiPE commands."""
    
    def __init__(self):
        self._commands: Dict[str, BaseCommand] = {}
        self._categories: Dict[str, List[str]] = {}
        self.hooks = HookManager()
        
    def register(self, command: BaseCommand) -> None:
        """Register a command."""
        if not isinstance(command, BaseCommand):
            raise ValueError("Command must inherit from BaseCommand")
            
        command_name = command.name.lower()
        
        if command_name in self._commands:
            raise ValueError(f"Command '{command_name}' already registered")
            
        self._commands[command_name] = command
        
        # Add to category
        category = command.category.lower()
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(command_name)
        
        # Execute post-registration hooks
        asyncio.create_task(self.hooks.trigger('command_registered', command))
        
    def register_class(self, command_class: Type[BaseCommand]) -> None:
        """Register a command class (instantiates it automatically)."""
        command = command_class()
        self.register(command)
        
    def unregister(self, command_name: str) -> None:
        """Unregister a command."""
        command_name = command_name.lower()
        
        if command_name not in self._commands:
            return
            
        command = self._commands[command_name]
        category = command.category.lower()
        
        # Remove from commands
        del self._commands[command_name]
        
        # Remove from category
        if category in self._categories and command_name in self._categories[category]:
            self._categories[category].remove(command_name)
            
        # Execute post-unregistration hooks
        asyncio.create_task(self.hooks.trigger('command_unregistered', command))
        
    def get_command(self, command_name: str) -> Optional[BaseCommand]:
        """Get a command by name."""
        return self._commands.get(command_name.lower())
        
    def get_commands_by_category(self, category: str) -> List[BaseCommand]:
        """Get all commands in a category."""
        category = category.lower()
        if category not in self._categories:
            return []
            
        return [self._commands[name] for name in self._categories[category]]
        
    def get_all_commands(self) -> List[BaseCommand]:
        """Get all registered commands."""
        return list(self._commands.values())
        
    def get_categories(self) -> List[str]:
        """Get all command categories."""
        return list(self._categories.keys())
        
    def search_commands(self, query: str) -> List[BaseCommand]:
        """Search commands by name or description."""
        query = query.lower()
        results = []
        
        for command in self._commands.values():
            if (query in command.name.lower() or 
                query in command.description.lower() or
                query in command.category.lower()):
                results.append(command)
                
        return results
        
    def list_commands(self, category: Optional[str] = None) -> List[CommandInfo]:
        """List command information."""
        if category:
            commands = self.get_commands_by_category(category)
        else:
            commands = self.get_all_commands()
            
        return [cmd.get_info() for cmd in commands]


# Built-in commands
class EchoCommand(BaseCommand):
    """Echo command - outputs input data."""
    
    name = 'echo'
    description = 'Echo input data to output'
    category = 'utility'
    input_types = ['any']
    output_types = ['any']
    
    async def execute(self, data: Any, *args, **kwargs) -> Any:
        """Echo the input data."""
        return data


class FilterCommand(BaseCommand):
    """Filter command - filters data based on conditions."""
    
    name = 'filter'
    description = 'Filter data based on conditions'
    category = 'data'
    input_types = ['list', 'dict']
    output_types = ['list', 'dict']
    
    async def execute(self, data: Any, *args, **kwargs) -> Any:
        """Filter data based on conditions."""
        condition = kwargs.get('condition')
        if not condition:
            return data
            
        if isinstance(data, list):
            return [item for item in data if self._evaluate_condition(item, condition)]
        elif isinstance(data, dict):
            return {k: v for k, v in data.items() if self._evaluate_condition(v, condition)}
        else:
            return data
    
    def _evaluate_condition(self, item: Any, condition: str) -> bool:
        """Evaluate a condition against an item."""
        try:
            return eval(condition, {"__builtins__": {}}, {'item': item})
        except:
            return False


class TransformCommand(BaseCommand):
    """Transform command - transforms data using expressions."""
    
    name = 'transform'
    description = 'Transform data using expressions'
    category = 'data'
    input_types = ['any']
    output_types = ['any']
    
    async def execute(self, data: Any, *args, **kwargs) -> Any:
        """Transform data using expressions."""
        expression = kwargs.get('expression')
        if not expression:
            return data
            
        try:
            # Simple expression evaluation - can be extended
            return eval(expression, {"__builtins__": {}}, {'data': data})
        except Exception as e:
            raise ValueError(f"Invalid transform expression: {e}")


# Auto-register built-in commands
def _register_builtin_commands(registry: CommandRegistry) -> None:
    """Register built-in commands."""
    builtin_commands = [
        EchoCommand,
        FilterCommand,
        TransformCommand,
    ]
    
    for command_class in builtin_commands:
        registry.register_class(command_class)
