"""
Service Resolution - Dependency resolution and service instantiation.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from dataclasses import dataclass
import logging
import inspect

from .container import Container, ServiceDescriptor, ServiceLifetime

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ResolutionContext:
    """サービス解決コンテキスト"""
    container: Container
    service_type: Type[T]
    service_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    depth: int = 0
    max_depth: int = 100
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class ServiceResolver:
    """サービス解決クラス"""
    
    def __init__(self, container: Container):
        self.container = container
        logger.debug("Initialized ServiceResolver")
    
    def resolve(self, service_type: Type[T], service_name: Optional[str] = None, 
                **parameters) -> T:
        """サービスを解決"""
        context = ResolutionContext(
            container=self.container,
            service_type=service_type,
            service_name=service_name,
            parameters=parameters
        )
        
        return self._resolve_service(context)
    
    def _resolve_service(self, context: ResolutionContext) -> Any:
        """サービスを解決（内部実装）"""
        if context.depth > context.max_depth:
            raise RuntimeError(f"Circular dependency detected at depth {context.depth}")
        
        # サービス記述子を取得
        descriptor = self._get_service_descriptor(context)
        if not descriptor:
            raise ValueError(f"Service not registered: {context.service_type}")
        
        # ライフタイムに応じて解決
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            return self._resolve_singleton(descriptor, context)
        elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
            return self._resolve_transient(descriptor, context)
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            return self._resolve_scoped(descriptor, context)
        else:
            raise ValueError(f"Unknown service lifetime: {descriptor.lifetime}")
    
    def _get_service_descriptor(self, context: ResolutionContext) -> Optional[ServiceDescriptor]:
        """サービス記述子を取得"""
        if context.service_name:
            return self.container.get_service_by_name(context.service_name)
        else:
            return self.container.get_service(context.service_type)
    
    def _resolve_singleton(self, descriptor: ServiceDescriptor, context: ResolutionContext) -> Any:
        """シングルトンサービスを解決"""
        if descriptor.instance is not None:
            return descriptor.instance
        
        # インスタンスを作成
        instance = self._create_instance(descriptor, context)
        descriptor.instance = instance
        return instance
    
    def _resolve_transient(self, descriptor: ServiceDescriptor, context: ResolutionContext) -> Any:
        """一時的サービスを解決"""
        return self._create_instance(descriptor, context)
    
    def _resolve_scoped(self, descriptor: ServiceDescriptor, context: ResolutionContext) -> Any:
        """スコープ付きサービスを解決"""
        # 現在のスコープから取得を試行
        if hasattr(self.container, 'current_scope'):
            scope = self.container.current_scope
            if scope and descriptor.service_type in scope:
                return scope[descriptor.service_type]
        
        # 新しいインスタンスを作成
        instance = self._create_instance(descriptor, context)
        
        # スコープに保存
        if hasattr(self.container, 'current_scope') and self.container.current_scope:
            self.container.current_scope[descriptor.service_type] = instance
        
        return instance
    
    def _create_instance(self, descriptor: ServiceDescriptor, context: ResolutionContext) -> Any:
        """インスタンスを作成"""
        if descriptor.factory:
            # ファクトリを使用
            return self._invoke_factory(descriptor.factory, context)
        elif descriptor.implementation_type:
            # 実装型を使用
            return self._create_from_type(descriptor.implementation_type, context)
        else:
            raise ValueError("Service descriptor must have factory or implementation type")
    
    def _invoke_factory(self, factory: callable, context: ResolutionContext) -> Any:
        """ファクトリを呼び出し"""
        try:
            # ファクトリの引数を解決
            sig = inspect.signature(factory)
            args = []
            kwargs = {}
            
            for param_name, param in sig.parameters.items():
                if param_name in context.parameters:
                    kwargs[param_name] = context.parameters[param_name]
                elif param.default != inspect.Parameter.empty:
                    kwargs[param_name] = param.default
                elif param.annotation != inspect.Parameter.empty:
                    # 依存関係を解決
                    if param.annotation != inspect.Parameter.empty:
                        dep_context = ResolutionContext(
                            container=context.container,
                            service_type=param.annotation,
                            depth=context.depth + 1,
                            max_depth=context.max_depth
                        )
                        args.append(self._resolve_service(dep_context))
            
            return factory(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error invoking factory {factory.__name__}: {e}")
            raise
    
    def _create_from_type(self, implementation_type: Type, context: ResolutionContext) -> Any:
        """型からインスタンスを作成"""
        try:
            # コンストラクタの引数を解決
            sig = inspect.signature(implementation_type.__init__)
            args = []
            kwargs = {}
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                if param_name in context.parameters:
                    kwargs[param_name] = context.parameters[param_name]
                elif param.default != inspect.Parameter.empty:
                    kwargs[param_name] = param.default
                elif param.annotation != inspect.Parameter.empty:
                    # 依存関係を解決
                    dep_context = ResolutionContext(
                        container=context.container,
                        service_type=param.annotation,
                        depth=context.depth + 1,
                        max_depth=context.max_depth
                    )
                    args.append(self._resolve_service(dep_context))
            
            return implementation_type(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error creating instance of {implementation_type.__name__}: {e}")
            raise
    
    def can_resolve(self, service_type: Type[T], service_name: Optional[str] = None) -> bool:
        """サービスが解決可能かチェック"""
        try:
            descriptor = self._get_service_descriptor(ResolutionContext(
                container=self.container,
                service_type=service_type,
                service_name=service_name
            ))
            return descriptor is not None
        except Exception:
            return False
    
    def get_all_services(self, service_type: Type[T]) -> List[T]:
        """指定された型のすべてのサービスを取得"""
        services = []
        descriptors = self.container.get_all_services(service_type)
        
        for descriptor in descriptors:
            try:
                context = ResolutionContext(
                    container=self.container,
                    service_type=service_type
                )
                service = self._resolve_service(context)
                services.append(service)
            except Exception as e:
                logger.warning(f"Failed to resolve service {descriptor.service_type}: {e}")
        
        return services
