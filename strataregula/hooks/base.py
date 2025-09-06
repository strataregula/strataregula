"""
Basic Hook Management System - Minimal implementation for v0.3.0
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class Hook:
    name: str
    callback: Callable
    hook_type: str


class HookManager:
    """Basic hook management for plugin system compatibility."""

    def __init__(self, logger=None) -> None:
        self.hooks: Dict[str, List[Hook]] = {}
        self.logger = logger or logging.getLogger(f"{__name__}.HookManager")

    def register_hook(self, hook_name: str, callback: Callable, name: Optional[str] = None) -> bool:
        """Register a hook callback."""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        hook = Hook(name=name or f"hook_{len(self.hooks[hook_name])}", callback=callback, hook_type=hook_name)
        self.hooks[hook_name].append(hook)
        if self.logger:
            self.logger.debug(f"Registered hook: {hook_name} as {hook.name}")
        return True

    # 旧名互換
    def register(self, hook_name: str, callback: Callable, name: str = None) -> bool:
        """Register a hook callback (alternative interface)."""
        return self.register_hook(hook_name, callback, name)

    def unregister_hook(self, hook_name: str, callback: Callable) -> bool:
        """Unregister a hook callback."""
        if hook_name not in self.hooks:
            return False
        before = len(self.hooks[hook_name])
        self.hooks[hook_name] = [h for h in self.hooks[hook_name] if h.callback is not callback]
        return len(self.hooks[hook_name]) < before

    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all callbacks for a hook."""
        results = []
        for hook in self.hooks.get(hook_name, []):
            try:
                results.append(hook.callback(*args, **kwargs))
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Hook {hook_name} callback failed: {e}")
        return results

    # Alias for compatibility
    def run_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all callbacks for a hook."""
        return self.execute_hook(hook_name, *args, **kwargs)

    def list_hooks(self, hook_type: str = None) -> List[Hook]:
        """List hooks, optionally filtered by type."""
        if hook_type:
            return self.hooks.get(hook_type, [])
        all_hooks: List[Hook] = []
        for hs in self.hooks.values():
            all_hooks.extend(hs)
        return all_hooks

    def list_hook_names(self) -> List[str]:
        """List all registered hook type names."""
        return list(self.hooks.keys())
