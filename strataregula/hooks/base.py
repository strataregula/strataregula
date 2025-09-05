"""
Basic Hook Management System - Minimal implementation for v0.3.0
"""

import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class HookManager:
    """Basic hook management for plugin system compatibility."""

    def __init__(self):
        self.hooks: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(f"{__name__}.HookManager")

    def register_hook(self, hook_name: str, callback: Callable) -> bool:
        """Register a hook callback."""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []

        self.hooks[hook_name].append(callback)
        self.logger.debug(f"Registered hook: {hook_name}")
        return True

    def register(self, hook_name: str, callback: Callable, name: str = None) -> bool:
        """Register a hook callback (alternative interface)."""
        return self.register_hook(hook_name, callback)

    def unregister_hook(self, hook_name: str, callback: Callable) -> bool:
        """Unregister a hook callback."""
        if hook_name in self.hooks and callback in self.hooks[hook_name]:
            self.hooks[hook_name].remove(callback)
            self.logger.debug(f"Unregistered hook: {hook_name}")
            return True
        return False

    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all callbacks for a hook."""
        results = []
        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                try:
                    result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Hook {hook_name} callback failed: {e}")
        return results

    def list_hooks(self, hook_name: str = None) -> List[str]:
        """List all registered hook names or callbacks for a specific hook."""
        if hook_name:
            return [cb.__name__ if hasattr(cb, '__name__') else str(cb) for cb in self.hooks.get(hook_name, [])]
        return list(self.hooks.keys())
