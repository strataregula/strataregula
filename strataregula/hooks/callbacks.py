"""
Callback Management - Callback registration and execution.
"""

from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
import logging
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class CallbackInfo:
    """コールバック情報"""
    name: str
    callback: Callable
    priority: int = 0
    enabled: bool = True
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CallbackRegistry:
    """コールバック登録管理"""
    
    def __init__(self):
        self.callbacks: Dict[str, CallbackInfo] = {}
        logger.debug("Initialized CallbackRegistry")
    
    def register(self, name: str, callback: Callable, priority: int = 0, 
                metadata: Optional[Dict[str, Any]] = None) -> bool:
        """コールバックを登録"""
        try:
            callback_info = CallbackInfo(
                name=name,
                callback=callback,
                priority=priority,
                metadata=metadata or {}
            )
            self.callbacks[name] = callback_info
            logger.debug(f"Registered callback: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register callback {name}: {e}")
            return False
    
    def unregister(self, name: str) -> bool:
        """コールバックを登録解除"""
        try:
            if name in self.callbacks:
                del self.callbacks[name]
                logger.debug(f"Unregistered callback: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unregister callback {name}: {e}")
            return False
    
    def get(self, name: str) -> Optional[CallbackInfo]:
        """コールバック情報を取得"""
        return self.callbacks.get(name)
    
    def list_callbacks(self) -> List[str]:
        """登録されているコールバック名の一覧を取得"""
        return list(self.callbacks.keys())
    
    def enable(self, name: str) -> bool:
        """コールバックを有効化"""
        if name in self.callbacks:
            self.callbacks[name].enabled = True
            logger.debug(f"Enabled callback: {name}")
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """コールバックを無効化"""
        if name in self.callbacks:
            self.callbacks[name].enabled = False
            logger.debug(f"Disabled callback: {name}")
            return True
        return False
    
    def clear(self) -> None:
        """すべてのコールバックをクリア"""
        self.callbacks.clear()
        logger.debug("Cleared all callbacks")


class CallbackManager:
    """コールバック実行管理"""
    
    def __init__(self, registry: Optional[CallbackRegistry] = None):
        self.registry = registry or CallbackRegistry()
        logger.debug("Initialized CallbackManager")
    
    def register_callback(self, name: str, callback: Callable, priority: int = 0,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """コールバックを登録"""
        return self.registry.register(name, callback, priority, metadata)
    
    async def execute_callback(self, name: str, *args, **kwargs) -> Any:
        """コールバックを実行"""
        callback_info = self.registry.get(name)
        if not callback_info:
            logger.warning(f"Callback not found: {name}")
            return None
        
        if not callback_info.enabled:
            logger.debug(f"Callback {name} is disabled")
            return None
        
        try:
            if asyncio.iscoroutinefunction(callback_info.callback):
                result = await callback_info.callback(*args, **kwargs)
            else:
                result = callback_info.callback(*args, **kwargs)
            
            logger.debug(f"Executed callback: {name}")
            return result
        except Exception as e:
            logger.error(f"Error executing callback {name}: {e}")
            raise
    
    async def execute_callbacks(self, names: List[str], *args, **kwargs) -> List[Any]:
        """複数のコールバックを実行"""
        results = []
        for name in names:
            try:
                result = await self.execute_callback(name, *args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to execute callback {name}: {e}")
                results.append(None)
        return results
    
    async def execute_all_callbacks(self, *args, **kwargs) -> List[Any]:
        """すべてのコールバックを実行（優先順位順）"""
        # 優先順位でソート
        sorted_callbacks = sorted(
            self.registry.callbacks.values(),
            key=lambda x: x.priority,
            reverse=True
        )
        
        results = []
        for callback_info in sorted_callbacks:
            if callback_info.enabled:
                try:
                    if asyncio.iscoroutinefunction(callback_info.callback):
                        result = await callback_info.callback(*args, **kwargs)
                    else:
                        result = callback_info.callback(*args, **kwargs)
                    results.append((callback_info.name, result))
                except Exception as e:
                    logger.error(f"Error executing callback {callback_info.name}: {e}")
                    results.append((callback_info.name, None))
        
        return results
    
    def get_callback_count(self) -> int:
        """コールバック数を取得"""
        return len(self.registry.callbacks)
    
    def get_enabled_callback_count(self) -> int:
        """有効なコールバック数を取得"""
        return sum(1 for cb in self.registry.callbacks.values() if cb.enabled)
    
    def list_callbacks(self) -> List[str]:
        """コールバック名の一覧を取得"""
        return self.registry.list_callbacks()
    
    def get_callback_info(self, name: str) -> Optional[CallbackInfo]:
        """コールバック情報を取得"""
        return self.registry.get(name)
