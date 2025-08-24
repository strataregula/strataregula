"""
Base Hook System - Core functionality for hooks, triggers, and callbacks.
"""

import asyncio
from typing import Any, Dict, List, Optional, Union, Callable, Coroutine
from dataclasses import dataclass, field
from enum import Enum
import inspect
import logging

logger = logging.getLogger(__name__)


class HookType(Enum):
    """Types of hooks available in the system."""
    PRE_PROCESS = "pre_process"
    POST_PROCESS = "post_process"
    PRE_COMMAND = "pre_command"
    POST_COMMAND = "post_command"
    PRE_CHAIN = "pre_chain"
    POST_CHAIN = "post_chain"
    ERROR = "error"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    CUSTOM = "custom"


@dataclass
class HookCallback:
    """Represents a hook callback function."""
    name: str
    callback: Callable
    hook_type: HookType
    priority: int = 0
    async_support: bool = False
    description: str = ""
    enabled: bool = True
    
    def __post_init__(self):
        """Initialize async_support based on callback inspection."""
        if self.async_support is None:
            self.async_support = inspect.iscoroutinefunction(self.callback)
    
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the hook callback."""
        if not self.enabled:
            return None
            
        try:
            if self.async_support:
                return await self.callback(*args, **kwargs)
            else:
                # Run sync callback in executor
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.callback, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing hook '{self.name}': {e}")
            raise


class HookRegistry:
    """Registry for managing hook callbacks."""
    
    def __init__(self):
        self._hooks: Dict[HookType, List[HookCallback]] = {
            hook_type: [] for hook_type in HookType
        }
        self._callbacks: Dict[str, HookCallback] = {}
        
    def register(self, hook_type: HookType, callback: Callable, 
                name: Optional[str] = None, priority: int = 0,
                description: str = "") -> str:
        """Register a hook callback."""
        if name is None:
            name = f"{hook_type.value}_{id(callback)}"
            
        if name in self._callbacks:
            raise ValueError(f"Hook callback '{name}' already registered")
            
        hook_callback = HookCallback(
            name=name,
            callback=callback,
            hook_type=hook_type,
            priority=priority,
            description=description
        )
        
        self._callbacks[name] = hook_callback
        self._hooks[hook_type].append(hook_callback)
        
        # Sort by priority (higher priority first)
        self._hooks[hook_type].sort(key=lambda x: x.priority, reverse=True)
        
        logger.debug(f"Registered hook '{name}' for type '{hook_type.value}'")
        return name
        
    def unregister(self, name: str) -> bool:
        """Unregister a hook callback."""
        if name not in self._callbacks:
            return False
            
        hook_callback = self._callbacks[name]
        self._hooks[hook_callback.hook_type].remove(hook_callback)
        del self._callbacks[name]
        
        logger.debug(f"Unregistered hook '{name}'")
        return True
        
    def get_callbacks(self, hook_type: HookType) -> List[HookCallback]:
        """Get all callbacks for a hook type."""
        return self._hooks[hook_type].copy()
        
    def get_callback(self, name: str) -> Optional[HookCallback]:
        """Get a specific callback by name."""
        return self._callbacks.get(name)
        
    def list_hooks(self, hook_type: Optional[HookType] = None) -> List[HookCallback]:
        """List all registered hooks, optionally filtered by type."""
        if hook_type:
            return self._hooks[hook_type].copy()
        else:
            return list(self._callbacks.values())
            
    def clear_hooks(self, hook_type: Optional[HookType] = None) -> None:
        """Clear all hooks, optionally filtered by type."""
        if hook_type:
            hooks_to_remove = self._hooks[hook_type].copy()
            for hook in hooks_to_remove:
                del self._callbacks[hook.name]
            self._hooks[hook_type].clear()
        else:
            self._callbacks.clear()
            for hook_type in HookType:
                self._hooks[hook_type].clear()


class HookManager:
    """Main hook manager for executing hooks."""
    
    def __init__(self):
        self.registry = HookRegistry()
        self.enabled = True
        
    def register(self, hook_type: Union[str, HookType], callback: Callable,
                name: Optional[str] = None, priority: int = 0,
                description: str = "") -> str:
        """Register a hook callback."""
        if isinstance(hook_type, str):
            try:
                hook_type = HookType(hook_type)
            except ValueError:
                # Create custom hook type
                hook_type = HookType.CUSTOM
                
        return self.registry.register(hook_type, callback, name, priority, description)
        
    def unregister(self, name: str) -> bool:
        """Unregister a hook callback."""
        return self.registry.unregister(name)
        
    async def trigger(self, hook_type: Union[str, HookType], 
                     *args, **kwargs) -> List[Any]:
        """Trigger all hooks of a specific type."""
        if not self.enabled:
            return []
            
        if isinstance(hook_type, str):
            try:
                hook_type = HookType(hook_type)
            except ValueError:
                # Custom hook type
                hook_type = HookType.CUSTOM
                
        callbacks = self.registry.get_callbacks(hook_type)
        results = []
        
        for callback in callbacks:
            try:
                result = await callback.execute(*args, **kwargs)
                if result is not None:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error in hook '{callback.name}': {e}")
                # Continue with other hooks
                continue
                
        return results
        
    def trigger_sync(self, hook_type: Union[str, HookType], 
                    *args, **kwargs) -> List[Any]:
        """Trigger hooks synchronously."""
        return asyncio.run(self.trigger(hook_type, *args, **kwargs))
        
    def get_registered_hooks(self) -> Dict[str, List[str]]:
        """Get a summary of registered hooks by type."""
        summary = {}
        for hook_type in HookType:
            callbacks = self.registry.get_callbacks(hook_type)
            summary[hook_type.value] = [cb.name for cb in callbacks]
        return summary
        
    def enable(self) -> None:
        """Enable hook execution."""
        self.enabled = True
        
    def disable(self) -> None:
        """Disable hook execution."""
        self.enabled = False
        
    def is_enabled(self) -> bool:
        """Check if hooks are enabled."""
        return self.enabled
        
    def clear_all(self) -> None:
        """Clear all registered hooks."""
        self.registry.clear_hooks()
        
    def list_hooks(self, hook_type: Optional[Union[str, HookType]] = None) -> List[HookCallback]:
        """List registered hooks."""
        if isinstance(hook_type, str):
            try:
                hook_type = HookType(hook_type)
            except ValueError:
                hook_type = None
                
        return self.registry.list_hooks(hook_type)
