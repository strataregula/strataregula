"""
Dependency Injection Container - Core IoC container implementation.
"""

import inspect
from typing import Any, Dict, List, Optional, Union, Type, Callable, TypeVar
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime options."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """Descriptor for a registered service."""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_resolved(self) -> bool:
        """Check if the service has been resolved."""
        return self.instance is not None
    
    def can_resolve(self) -> bool:
        """Check if the service can be resolved."""
        return (self.implementation_type is not None or 
                self.factory is not None or 
                self.instance is not None)


class Container:
    """Main dependency injection container."""
    
    def __init__(self):
        self._services: Dict[Type, List[ServiceDescriptor]] = {}
        self._named_services: Dict[str, ServiceDescriptor] = {}
        self._resolved_instances: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._current_scope: Optional[str] = None
        
    def register(self, service_type: Type[T], 
                implementation_type: Optional[Type[T]] = None,
                factory: Optional[Callable] = None,
                instance: Optional[T] = None,
                lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
                name: Optional[str] = None) -> 'Container':
        """Register a service in the container."""
        if service_type not in self._services:
            self._services[service_type] = []
            
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            instance=instance,
            lifetime=lifetime,
            name=name
        )
        
        self._services[service_type].append(descriptor)
        
        # Register named service if provided
        if name:
            self._named_services[name] = descriptor
            
        logger.debug(f"Registered service {service_type.__name__} with lifetime {lifetime.value}")
        return self
        
    def register_singleton(self, service_type: Type[T], 
                          implementation_type: Optional[Type[T]] = None,
                          factory: Optional[Callable] = None,
                          instance: Optional[T] = None,
                          name: Optional[str] = None) -> 'Container':
        """Register a singleton service."""
        return self.register(
            service_type, implementation_type, factory, instance,
            ServiceLifetime.SINGLETON, name
        )
        
    def register_transient(self, service_type: Type[T],
                          implementation_type: Optional[Type[T]] = None,
                          factory: Optional[Callable] = None,
                          name: Optional[str] = None) -> 'Container':
        """Register a transient service."""
        return self.register(
            service_type, implementation_type, factory, None,
            ServiceLifetime.TRANSIENT, name
        )
        
    def register_scoped(self, service_type: Type[T],
                       implementation_type: Optional[Type[T]] = None,
                       factory: Optional[Callable] = None,
                       name: Optional[str] = None) -> 'Container':
        """Register a scoped service."""
        return self.register(
            service_type, implementation_type, factory, None,
            ServiceLifetime.SCOPED, name
        )
        
    def resolve(self, service_type: Type[T], name: Optional[str] = None) -> T:
        """Resolve a service from the container."""
        if name and name in self._named_services:
            descriptor = self._named_services[name]
            return self._resolve_descriptor(descriptor)
            
        if service_type not in self._services:
            raise ValueError(f"Service {service_type.__name__} not registered")
            
        descriptors = self._services[service_type]
        if not descriptors:
            raise ValueError(f"No implementations found for {service_type.__name__}")
            
        # Use the first available descriptor
        descriptor = descriptors[0]
        return self._resolve_descriptor(descriptor)
        
    def resolve_all(self, service_type: Type[T]) -> List[T]:
        """Resolve all implementations of a service type."""
        if service_type not in self._services:
            return []
            
        return [self._resolve_descriptor(desc) for desc in self._services[service_type]]
        
    def try_resolve(self, service_type: Type[T], name: Optional[str] = None) -> Optional[T]:
        """Try to resolve a service, returns None if not found."""
        try:
            return self.resolve(service_type, name)
        except (ValueError, Exception):
            return None
            
    def _resolve_descriptor(self, descriptor: ServiceDescriptor) -> Any:
        """Resolve a service descriptor."""
        # Check if already resolved for singleton
        if descriptor.lifetime == ServiceLifetime.SINGLETON and descriptor.is_resolved():
            return descriptor.instance
            
        # Check if already resolved in current scope
        if descriptor.lifetime == ServiceLifetime.SCOPED and self._current_scope:
            scope_key = f"{self._current_scope}_{descriptor.service_type.__name__}"
            if scope_key in self._scoped_instances:
                return self._scoped_instances[scope_key]
                
        # Create new instance
        instance = self._create_instance(descriptor)
        
        # Store instance based on lifetime
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            descriptor.instance = instance
        elif descriptor.lifetime == ServiceLifetime.SCOPED and self._current_scope:
            scope_key = f"{self._current_scope}_{descriptor.service_type.__name__}"
            if scope_key not in self._scoped_instances:
                self._scoped_instances[scope_key] = {}
            self._scoped_instances[scope_key][descriptor.service_type] = instance
            
        return instance
        
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create a new instance of a service."""
        if descriptor.instance is not None:
            return descriptor.instance
            
        if descriptor.factory is not None:
            return descriptor.factory()
            
        if descriptor.implementation_type is not None:
            return self._create_instance_from_type(descriptor.implementation_type)
            
        raise ValueError(f"Cannot create instance for {descriptor.service_type.__name__}")
        
    def _create_instance_from_type(self, implementation_type: Type) -> Any:
        """Create an instance from a type using constructor injection."""
        constructor = self._get_constructor(implementation_type)
        if not constructor:
            return implementation_type()
            
        # Get constructor parameters
        sig = inspect.signature(constructor)
        params = {}
        
        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                try:
                    param_value = self.resolve(param.annotation)
                    params[param_name] = param_value
                except Exception as e:
                    logger.warning(f"Could not resolve parameter {param_name}: {e}")
                    if param.default != inspect.Parameter.empty:
                        params[param_name] = param.default
                    else:
                        raise ValueError(f"Required parameter {param_name} could not be resolved")
                        
        return constructor(**params)
        
    def _get_constructor(self, cls: Type) -> Optional[Callable]:
        """Get the constructor for a class."""
        if hasattr(cls, '__init__') and cls.__init__ != object.__init__:
            return cls.__init__
        return None
        
    def create_scope(self, scope_name: str) -> 'Container':
        """Create a new scoped container."""
        scoped_container = Container()
        scoped_container._current_scope = scope_name
        scoped_container._services = self._services.copy()
        scoped_container._named_services = self._named_services.copy()
        return scoped_container
        
    def dispose(self) -> None:
        """Dispose of the container and all resolved instances."""
        self._resolved_instances.clear()
        self._scoped_instances.clear()
        
    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered."""
        return service_type in self._services and len(self._services[service_type]) > 0
        
    def get_registered_services(self) -> List[Type]:
        """Get all registered service types."""
        return list(self._services.keys())
        
    def get_service_info(self, service_type: Type) -> List[ServiceDescriptor]:
        """Get information about registered services of a type."""
        return self._services.get(service_type, []).copy()
