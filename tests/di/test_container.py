"""
Unit tests for dependency injection container

Tests for Container, ServiceDescriptor, and ServiceLifetime functionality.
"""

import pytest
from typing import Protocol, Optional
from unittest.mock import Mock

from strataregula.di.container import (
    Container, ServiceDescriptor, ServiceLifetime
)


# Test interfaces and classes
class ITestService(Protocol):
    def get_value(self) -> str: ...


class TestService:
    def get_value(self) -> str:
        return "test_value"


class TestServiceWithDependency:
    def __init__(self, dependency: ITestService):
        self.dependency = dependency
    
    def get_dependency_value(self) -> str:
        return self.dependency.get_value()


class TestServiceWithOptionalDependency:
    def __init__(self, dependency: Optional[ITestService] = None):
        self.dependency = dependency
    
    def has_dependency(self) -> bool:
        return self.dependency is not None


class TestServiceWithMultipleDependencies:
    def __init__(self, service1: ITestService, service2: Optional[str] = "default"):
        self.service1 = service1
        self.service2 = service2


class TestServiceDescriptor:
    """Test ServiceDescriptor functionality"""
    
    def test_descriptor_creation(self):
        """Test creating service descriptor"""
        descriptor = ServiceDescriptor(
            service_type=ITestService,
            implementation_type=TestService,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        assert descriptor.service_type == ITestService
        assert descriptor.implementation_type == TestService
        assert descriptor.lifetime == ServiceLifetime.SINGLETON
        assert descriptor.instance is None
        assert descriptor.factory is None
        assert descriptor.name is None
    
    def test_descriptor_with_factory(self):
        """Test descriptor with factory function"""
        factory = lambda: TestService()
        
        descriptor = ServiceDescriptor(
            service_type=ITestService,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT
        )
        
        assert descriptor.service_type == ITestService
        assert descriptor.factory == factory
        assert descriptor.implementation_type is None
    
    def test_descriptor_with_instance(self):
        """Test descriptor with pre-created instance"""
        instance = TestService()
        
        descriptor = ServiceDescriptor(
            service_type=ITestService,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        assert descriptor.service_type == ITestService
        assert descriptor.instance == instance
    
    def test_descriptor_is_resolved(self):
        """Test is_resolved property"""
        descriptor = ServiceDescriptor(service_type=ITestService)
        
        assert not descriptor.is_resolved()
        
        descriptor.instance = TestService()
        assert descriptor.is_resolved()
    
    def test_descriptor_can_resolve(self):
        """Test can_resolve property"""
        # No implementation
        descriptor = ServiceDescriptor(service_type=ITestService)
        assert not descriptor.can_resolve()
        
        # With implementation type
        descriptor.implementation_type = TestService
        assert descriptor.can_resolve()
        
        # With factory
        descriptor = ServiceDescriptor(
            service_type=ITestService,
            factory=lambda: TestService()
        )
        assert descriptor.can_resolve()
        
        # With instance
        descriptor = ServiceDescriptor(
            service_type=ITestService,
            instance=TestService()
        )
        assert descriptor.can_resolve()


class TestContainer:
    """Test Container functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.container = Container()
    
    def test_container_initialization(self):
        """Test container initialization"""
        assert len(self.container._services) == 0
        assert len(self.container._named_services) == 0
        assert len(self.container._resolved_instances) == 0
    
    def test_register_transient(self):
        """Test registering transient service"""
        self.container.register(ITestService, TestService, lifetime=ServiceLifetime.TRANSIENT)
        
        assert self.container.is_registered(ITestService)
        descriptors = self.container.get_service_info(ITestService)
        assert len(descriptors) == 1
        assert descriptors[0].lifetime == ServiceLifetime.TRANSIENT
    
    def test_register_singleton(self):
        """Test registering singleton service"""
        self.container.register_singleton(ITestService, TestService)
        
        descriptors = self.container.get_service_info(ITestService)
        assert descriptors[0].lifetime == ServiceLifetime.SINGLETON
    
    def test_register_scoped(self):
        """Test registering scoped service"""
        self.container.register_scoped(ITestService, TestService)
        
        descriptors = self.container.get_service_info(ITestService)
        assert descriptors[0].lifetime == ServiceLifetime.SCOPED
    
    def test_register_with_factory(self):
        """Test registering service with factory"""
        def factory() -> ITestService:
            return TestService()
        
        self.container.register(ITestService, factory=factory)
        
        service = self.container.resolve(ITestService)
        assert isinstance(service, TestService)
        assert service.get_value() == "test_value"
    
    def test_register_with_instance(self):
        """Test registering service with instance"""
        instance = TestService()
        self.container.register(ITestService, instance=instance)
        
        resolved = self.container.resolve(ITestService)
        assert resolved is instance
    
    def test_register_named_service(self):
        """Test registering named service"""
        self.container.register(ITestService, TestService, name="test_service")
        
        assert "test_service" in self.container._named_services
        
        service = self.container.resolve(ITestService, name="test_service")
        assert isinstance(service, TestService)
    
    def test_resolve_transient(self):
        """Test resolving transient service creates new instances"""
        self.container.register_transient(ITestService, TestService)
        
        service1 = self.container.resolve(ITestService)
        service2 = self.container.resolve(ITestService)
        
        assert isinstance(service1, TestService)
        assert isinstance(service2, TestService)
        assert service1 is not service2  # Different instances
    
    def test_resolve_singleton(self):
        """Test resolving singleton service returns same instance"""
        self.container.register_singleton(ITestService, TestService)
        
        service1 = self.container.resolve(ITestService)
        service2 = self.container.resolve(ITestService)
        
        assert isinstance(service1, TestService)
        assert isinstance(service2, TestService)
        assert service1 is service2  # Same instance
    
    def test_resolve_with_dependency(self):
        """Test resolving service with dependency injection"""
        self.container.register_singleton(ITestService, TestService)
        self.container.register_transient(TestServiceWithDependency)
        
        service = self.container.resolve(TestServiceWithDependency)
        
        assert isinstance(service, TestServiceWithDependency)
        assert service.get_dependency_value() == "test_value"
    
    def test_resolve_with_optional_dependency(self):
        """Test resolving service with optional dependency"""
        # Register service without its dependency
        self.container.register_transient(TestServiceWithOptionalDependency)
        
        service = self.container.resolve(TestServiceWithOptionalDependency)
        
        assert isinstance(service, TestServiceWithOptionalDependency)
        assert not service.has_dependency()
    
    def test_resolve_with_multiple_dependencies(self):
        """Test resolving service with multiple dependencies"""
        self.container.register_singleton(ITestService, TestService)
        self.container.register_transient(TestServiceWithMultipleDependencies)
        
        service = self.container.resolve(TestServiceWithMultipleDependencies)
        
        assert isinstance(service, TestServiceWithMultipleDependencies)
        assert service.service1.get_value() == "test_value"
        assert service.service2 == "default"
    
    def test_resolve_unregistered_service(self):
        """Test resolving unregistered service raises error"""
        with pytest.raises(ValueError, match="Service ITestService not registered"):
            self.container.resolve(ITestService)
    
    def test_resolve_all(self):
        """Test resolving all implementations of a service"""
        # Register multiple implementations
        self.container.register(ITestService, TestService, name="impl1")
        self.container.register(ITestService, TestService, name="impl2")
        
        services = self.container.resolve_all(ITestService)
        
        assert len(services) == 2
        assert all(isinstance(s, TestService) for s in services)
    
    def test_resolve_all_empty(self):
        """Test resolving all when no services registered"""
        services = self.container.resolve_all(ITestService)
        
        assert len(services) == 0
    
    def test_try_resolve_success(self):
        """Test try_resolve with registered service"""
        self.container.register_transient(ITestService, TestService)
        
        service = self.container.try_resolve(ITestService)
        
        assert service is not None
        assert isinstance(service, TestService)
    
    def test_try_resolve_failure(self):
        """Test try_resolve with unregistered service"""
        service = self.container.try_resolve(ITestService)
        
        assert service is None
    
    def test_try_resolve_named(self):
        """Test try_resolve with named service"""
        self.container.register(ITestService, TestService, name="test")
        
        service = self.container.try_resolve(ITestService, name="test")
        assert service is not None
        
        service = self.container.try_resolve(ITestService, name="nonexistent")
        assert service is None
    
    def test_create_scope(self):
        """Test creating scoped container"""
        # Register services in parent container
        self.container.register_singleton(ITestService, TestService)
        self.container.register_scoped(TestServiceWithDependency)
        
        # Create scoped container
        scoped = self.container.create_scope("test_scope")
        
        assert scoped._current_scope == "test_scope"
        assert len(scoped._services) == len(self.container._services)
        
        # Resolve services in scope
        service1 = scoped.resolve(TestServiceWithDependency)
        service2 = scoped.resolve(TestServiceWithDependency)
        
        # Should be same instance within scope (scoped lifetime)
        assert service1 is service2
    
    def test_scoped_service_isolation(self):
        """Test scoped services are isolated between scopes"""
        self.container.register_singleton(ITestService, TestService)
        self.container.register_scoped(TestServiceWithDependency)
        
        scope1 = self.container.create_scope("scope1")
        scope2 = self.container.create_scope("scope2")
        
        service1 = scope1.resolve(TestServiceWithDependency)
        service2 = scope2.resolve(TestServiceWithDependency)
        
        # Should be different instances in different scopes
        assert service1 is not service2
    
    def test_singleton_shared_across_scopes(self):
        """Test singleton services are shared across scopes"""
        self.container.register_singleton(ITestService, TestService)
        
        scope1 = self.container.create_scope("scope1")
        scope2 = self.container.create_scope("scope2")
        
        service1 = scope1.resolve(ITestService)
        service2 = scope2.resolve(ITestService)
        parent_service = self.container.resolve(ITestService)
        
        # All should be same instance
        assert service1 is service2 is parent_service
    
    def test_dispose(self):
        """Test container disposal"""
        self.container.register_singleton(ITestService, TestService)
        
        # Resolve to create instances
        self.container.resolve(ITestService)
        
        # Create scoped instance
        scope = self.container.create_scope("test")
        scope.resolve(ITestService)
        
        # Dispose
        self.container.dispose()
        
        assert len(self.container._resolved_instances) == 0
        assert len(self.container._scoped_instances) == 0
    
    def test_is_registered(self):
        """Test is_registered method"""
        assert not self.container.is_registered(ITestService)
        
        self.container.register_transient(ITestService, TestService)
        
        assert self.container.is_registered(ITestService)
    
    def test_get_registered_services(self):
        """Test getting all registered service types"""
        services = self.container.get_registered_services()
        assert len(services) == 0
        
        self.container.register_transient(ITestService, TestService)
        self.container.register_singleton(str, instance="test")
        
        services = self.container.get_registered_services()
        assert len(services) == 2
        assert ITestService in services
        assert str in services
    
    def test_get_service_info(self):
        """Test getting service information"""
        # No services registered
        info = self.container.get_service_info(ITestService)
        assert len(info) == 0
        
        # Register services
        self.container.register_transient(ITestService, TestService, name="impl1")
        self.container.register_singleton(ITestService, TestService, name="impl2")
        
        info = self.container.get_service_info(ITestService)
        assert len(info) == 2
        
        # Check info details
        names = [desc.name for desc in info]
        assert "impl1" in names
        assert "impl2" in names
        
        lifetimes = [desc.lifetime for desc in info]
        assert ServiceLifetime.TRANSIENT in lifetimes
        assert ServiceLifetime.SINGLETON in lifetimes
    
    def test_chained_registration(self):
        """Test chained service registration"""
        result = (self.container
                 .register_singleton(ITestService, TestService)
                 .register_transient(str, instance="test")
                 .register_scoped(int, instance=42))
        
        assert result is self.container  # Should return self for chaining
        assert self.container.is_registered(ITestService)
        assert self.container.is_registered(str)
        assert self.container.is_registered(int)


class TestContainerEdgeCases:
    """Test container edge cases and error conditions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.container = Container()
    
    def test_resolve_circular_dependency(self):
        """Test resolving circular dependencies"""
        class ServiceA:
            def __init__(self, service_b: 'ServiceB'):
                self.service_b = service_b
        
        class ServiceB:
            def __init__(self, service_a: ServiceA):
                self.service_a = service_a
        
        self.container.register_transient(ServiceA)
        self.container.register_transient(ServiceB)
        
        # This should raise an error due to circular dependency
        with pytest.raises(Exception):  # Could be RecursionError or other
            self.container.resolve(ServiceA)
    
    def test_resolve_missing_required_dependency(self):
        """Test resolving service with missing required dependency"""
        class ServiceWithRequiredDep:
            def __init__(self, required_dep: str):  # str not registered
                self.required_dep = required_dep
        
        self.container.register_transient(ServiceWithRequiredDep)
        
        with pytest.raises(ValueError, match="Required parameter required_dep could not be resolved"):
            self.container.resolve(ServiceWithRequiredDep)
    
    def test_resolve_with_default_parameter(self):
        """Test resolving service with default parameter values"""
        class ServiceWithDefaults:
            def __init__(self, optional_param: str = "default_value"):
                self.optional_param = optional_param
        
        self.container.register_transient(ServiceWithDefaults)
        
        service = self.container.resolve(ServiceWithDefaults)
        assert service.optional_param == "default_value"
    
    def test_resolve_descriptor_invalid_configuration(self):
        """Test resolving descriptor with invalid configuration"""
        descriptor = ServiceDescriptor(service_type=ITestService)
        # No implementation, factory, or instance
        
        with pytest.raises(ValueError, match="Cannot create instance"):
            self.container._resolve_descriptor(descriptor)
    
    def test_register_multiple_implementations_resolve_first(self):
        """Test that resolve returns first registered implementation"""
        class TestService1(TestService):
            def get_value(self) -> str:
                return "service1"
        
        class TestService2(TestService):
            def get_value(self) -> str:
                return "service2"
        
        # Register multiple implementations
        self.container.register_transient(ITestService, TestService1)
        self.container.register_transient(ITestService, TestService2)
        
        # Should resolve to first registered
        service = self.container.resolve(ITestService)
        assert service.get_value() == "service1"
    
    def test_factory_with_exception(self):
        """Test factory function that raises exception"""
        def failing_factory():
            raise RuntimeError("Factory failed")
        
        self.container.register(ITestService, factory=failing_factory)
        
        with pytest.raises(RuntimeError, match="Factory failed"):
            self.container.resolve(ITestService)
    
    def test_constructor_with_exception(self):
        """Test constructor that raises exception"""
        class FailingService:
            def __init__(self):
                raise RuntimeError("Constructor failed")
        
        self.container.register_transient(FailingService)
        
        with pytest.raises(RuntimeError, match="Constructor failed"):
            self.container.resolve(FailingService)
    
    def test_named_service_priority(self):
        """Test that named service resolution takes priority"""
        self.container.register_transient(ITestService, TestService)
        
        # Register named service with different implementation
        class NamedTestService(TestService):
            def get_value(self) -> str:
                return "named_service"
        
        self.container.register(ITestService, NamedTestService, name="named")
        
        # Normal resolution
        normal_service = self.container.resolve(ITestService)
        assert normal_service.get_value() == "test_value"
        
        # Named resolution
        named_service = self.container.resolve(ITestService, name="named")
        assert named_service.get_value() == "named_service"


class TestServiceLifetime:
    """Test ServiceLifetime enum"""
    
    def test_lifetime_values(self):
        """Test lifetime enum values"""
        assert ServiceLifetime.SINGLETON.value == "singleton"
        assert ServiceLifetime.TRANSIENT.value == "transient"
        assert ServiceLifetime.SCOPED.value == "scoped"
    
    def test_lifetime_comparison(self):
        """Test lifetime comparisons"""
        assert ServiceLifetime.SINGLETON == ServiceLifetime.SINGLETON
        assert ServiceLifetime.SINGLETON != ServiceLifetime.TRANSIENT
    
    def test_lifetime_string_representation(self):
        """Test lifetime string representations"""
        assert str(ServiceLifetime.SINGLETON) == "ServiceLifetime.SINGLETON"