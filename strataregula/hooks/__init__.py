"""
Hook System - Event-driven hooks, triggers, and callbacks for strataregula.

A flexible system for adding custom behavior at various points
in the processing pipeline without modifying core code.
"""

from .base import HookManager, HookCallback, HookRegistry
from .triggers import TriggerManager, TriggerEvent
from .callbacks import CallbackManager, CallbackRegistry

__all__ = [
    'HookManager',
    'HookCallback', 
    'HookRegistry',
    'TriggerManager',
    'TriggerEvent',
    'CallbackManager',
    'CallbackRegistry',
]
