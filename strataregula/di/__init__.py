"""
Dependency Injection System - IoC container for strataregula.

A flexible dependency injection system that supports:
- Service registration and resolution
- Singleton and transient lifetimes
- Interface-based abstractions
- Configuration-driven injection
"""

from .container import Container, ServiceLifetime
from .resolver import ServiceResolver, ResolutionContext
from .providers import ServiceProvider, FactoryProvider, InstanceProvider

__all__ = [
    'Container',
    'ServiceLifetime',
    'ServiceResolver',
    'ResolutionContext',
    'ServiceProvider',
    'FactoryProvider',
    'InstanceProvider',
]
