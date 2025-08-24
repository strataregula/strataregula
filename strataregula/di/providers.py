"""
Service Providers - Different ways to provide service instances.
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from abc import ABC, abstractmethod
import logging

from .container import Container, ServiceDescriptor, ServiceLifetime

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceProvider(ABC):
    """サービスプロバイダーの基底クラス"""
    
    def __init__(self, container: Container):
        self.container = container
        logger.debug(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod
    def provide(self, service_type: Type[T], **kwargs) -> T:
        """サービスを提供"""
        pass
    
    def can_provide(self, service_type: Type[T]) -> bool:
        """サービスを提供できるかチェック"""
        return True


class FactoryProvider(ServiceProvider):
    """ファクトリベースのサービスプロバイダー"""
    
    def __init__(self, container: Container, factory: Callable[..., T]):
        super().__init__(container)
        self.factory = factory
        logger.debug(f"Initialized FactoryProvider with factory: {factory.__name__}")
    
    def provide(self, service_type: Type[T], **kwargs) -> T:
        """ファクトリを使用してサービスを提供"""
        try:
            # ファクトリの引数を解決
            resolved_kwargs = self._resolve_parameters(kwargs)
            result = self.factory(**resolved_kwargs)
            logger.debug(f"Provided service using factory: {self.factory.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error providing service with factory {self.factory.__name__}: {e}")
            raise
    
    def _resolve_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """パラメータを解決"""
        resolved = {}
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('@'):
                # 依存関係の参照
                service_name = value[1:]
                try:
                    service = self.container.resolve_by_name(service_name)
                    resolved[key] = service
                except Exception as e:
                    logger.warning(f"Could not resolve dependency {service_name}: {e}")
                    resolved[key] = value
            else:
                resolved[key] = value
        return resolved
    
    def can_provide(self, service_type: Type[T]) -> bool:
        """ファクトリが指定された型を提供できるかチェック"""
        try:
            # ファクトリの戻り値の型をチェック（可能な場合）
            import inspect
            sig = inspect.signature(self.factory)
            return sig.return_annotation == service_type or sig.return_annotation == inspect.Signature.empty
        except Exception:
            return True


class InstanceProvider(ServiceProvider):
    """インスタンスベースのサービスプロバイダー"""
    
    def __init__(self, container: Container, instance: T):
        super().__init__(container)
        self.instance = instance
        logger.debug(f"Initialized InstanceProvider with instance: {type(instance).__name__}")
    
    def provide(self, service_type: Type[T], **kwargs) -> T:
        """既存のインスタンスを提供"""
        if isinstance(self.instance, service_type):
            logger.debug(f"Provided existing instance: {type(self.instance).__name__}")
            return self.instance
        else:
            raise TypeError(f"Instance {type(self.instance).__name__} is not compatible with {service_type.__name__}")
    
    def can_provide(self, service_type: Type[T]) -> bool:
        """インスタンスが指定された型と互換性があるかチェック"""
        return isinstance(self.instance, service_type)


class TypeProvider(ServiceProvider):
    """型ベースのサービスプロバイダー"""
    
    def __init__(self, container: Container, implementation_type: Type[T]):
        super().__init__(container)
        self.implementation_type = implementation_type
        logger.debug(f"Initialized TypeProvider with type: {implementation_type.__name__}")
    
    def provide(self, service_type: Type[T], **kwargs) -> T:
        """型からインスタンスを作成して提供"""
        try:
            # コンストラクタの引数を解決
            resolved_kwargs = self._resolve_parameters(kwargs)
            instance = self.implementation_type(**resolved_kwargs)
            logger.debug(f"Provided service by creating instance: {self.implementation_type.__name__}")
            return instance
        except Exception as e:
            logger.error(f"Error creating instance of {self.implementation_type.__name__}: {e}")
            raise
    
    def _resolve_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """パラメータを解決"""
        resolved = {}
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('@'):
                # 依存関係の参照
                service_name = value[1:]
                try:
                    service = self.container.resolve_by_name(service_name)
                    resolved[key] = service
                except Exception as e:
                    logger.warning(f"Could not resolve dependency {service_name}: {e}")
                    resolved[key] = value
            else:
                resolved[key] = value
        return resolved
    
    def can_provide(self, service_type: Type[T]) -> bool:
        """型が指定されたサービス型と互換性があるかチェック"""
        return issubclass(self.implementation_type, service_type)


class LazyProvider(ServiceProvider):
    """遅延初期化のサービスプロバイダー"""
    
    def __init__(self, container: Container, provider_factory: Callable[[], ServiceProvider]):
        super().__init__(container)
        self.provider_factory = provider_factory
        self._provider: Optional[ServiceProvider] = None
        logger.debug("Initialized LazyProvider")
    
    def provide(self, service_type: Type[T], **kwargs) -> T:
        """遅延初期化されたプロバイダーからサービスを提供"""
        if self._provider is None:
            self._provider = self.provider_factory()
            logger.debug("Lazy provider initialized")
        
        return self._provider.provide(service_type, **kwargs)
    
    def can_provide(self, service_type: Type[T]) -> bool:
        """遅延初期化されたプロバイダーがサービスを提供できるかチェック"""
        if self._provider is None:
            self._provider = self.provider_factory()
        return self._provider.can_provide(service_type)


class CompositeProvider(ServiceProvider):
    """複数のプロバイダーを組み合わせたサービスプロバイダー"""
    
    def __init__(self, container: Container, providers: List[ServiceProvider]):
        super().__init__(container)
        self.providers = providers
        logger.debug(f"Initialized CompositeProvider with {len(providers)} providers")
    
    def provide(self, service_type: Type[T], **kwargs) -> T:
        """最初に見つかったプロバイダーからサービスを提供"""
        for provider in self.providers:
            if provider.can_provide(service_type):
                try:
                    return provider.provide(service_type, **kwargs)
                except Exception as e:
                    logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
                    continue
        
        raise ValueError(f"No provider can provide service: {service_type.__name__}")
    
    def can_provide(self, service_type: Type[T]) -> bool:
        """いずれかのプロバイダーがサービスを提供できるかチェック"""
        return any(provider.can_provide(service_type) for provider in self.providers)
    
    def add_provider(self, provider: ServiceProvider) -> None:
        """プロバイダーを追加"""
        self.providers.append(provider)
        logger.debug(f"Added provider: {provider.__class__.__name__}")
    
    def remove_provider(self, provider: ServiceProvider) -> bool:
        """プロバイダーを削除"""
        try:
            self.providers.remove(provider)
            logger.debug(f"Removed provider: {provider.__class__.__name__}")
            return True
        except ValueError:
            return False
