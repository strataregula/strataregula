"""
Base hook management system for StrataRegula.
"""

from typing import Any, Callable, Dict, List


class HookManager:
    """Basic hook manager for plugin lifecycle events."""
    
    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {}
    
    def register_hook(self, event: str, callback: Callable) -> None:
        """Register a hook callback for an event."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)
    
    def trigger_hook(self, event: str, *args, **kwargs) -> None:
        """Trigger all hooks for an event."""
        for callback in self._hooks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception:
                pass  # Ignore hook errors