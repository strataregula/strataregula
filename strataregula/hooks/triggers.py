"""
Trigger Management - Event-driven triggers and callbacks.
"""

from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """トリガーの種類"""
    BEFORE_EXECUTE = "before_execute"
    AFTER_EXECUTE = "after_execute"
    ON_ERROR = "on_error"
    ON_COMPLETE = "on_complete"
    CUSTOM = "custom"


@dataclass
class TriggerEvent:
    """トリガーイベント"""
    type: TriggerType
    name: str
    data: Any = None
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            import time
            self.timestamp = time.time()


class TriggerManager:
    """トリガー管理クラス"""
    
    def __init__(self):
        self.triggers: Dict[TriggerType, List[Callable]] = {
            trigger_type: [] for trigger_type in TriggerType
        }
        self.custom_triggers: Dict[str, List[Callable]] = {}
        logger.debug("Initialized TriggerManager")
    
    def register_trigger(self, trigger_type: TriggerType, callback: Callable) -> bool:
        """トリガーを登録"""
        try:
            self.triggers[trigger_type].append(callback)
            logger.debug(f"Registered trigger: {trigger_type.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to register trigger: {e}")
            return False
    
    def register_custom_trigger(self, name: str, callback: Callable) -> bool:
        """カスタムトリガーを登録"""
        try:
            if name not in self.custom_triggers:
                self.custom_triggers[name] = []
            self.custom_triggers[name].append(callback)
            logger.debug(f"Registered custom trigger: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register custom trigger: {e}")
            return False
    
    async def fire_trigger(self, trigger_type: TriggerType, event: TriggerEvent) -> None:
        """トリガーを発火"""
        callbacks = self.triggers.get(trigger_type, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
                logger.debug(f"Triggered {trigger_type.value}: {callback.__name__}")
            except Exception as e:
                logger.error(f"Error in trigger callback {callback.__name__}: {e}")
    
    async def fire_custom_trigger(self, name: str, event: TriggerEvent) -> None:
        """カスタムトリガーを発火"""
        callbacks = self.custom_triggers.get(name, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
                logger.debug(f"Triggered custom trigger {name}: {callback.__name__}")
            except Exception as e:
                logger.error(f"Error in custom trigger callback {callback.__name__}: {e}")
    
    def remove_trigger(self, trigger_type: TriggerType, callback: Callable) -> bool:
        """トリガーを削除"""
        try:
            if callback in self.triggers[trigger_type]:
                self.triggers[trigger_type].remove(callback)
                logger.debug(f"Removed trigger: {trigger_type.value}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove trigger: {e}")
            return False
    
    def remove_custom_trigger(self, name: str, callback: Callable) -> bool:
        """カスタムトリガーを削除"""
        try:
            if name in self.custom_triggers and callback in self.custom_triggers[name]:
                self.custom_triggers[name].remove(callback)
                logger.debug(f"Removed custom trigger: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove custom trigger: {e}")
            return False
    
    def get_trigger_count(self, trigger_type: TriggerType) -> int:
        """トリガーの数を取得"""
        return len(self.triggers.get(trigger_type, []))
    
    def get_custom_trigger_count(self, name: str) -> int:
        """カスタムトリガーの数を取得"""
        return len(self.custom_triggers.get(name, []))
    
    def clear_triggers(self, trigger_type: Optional[TriggerType] = None) -> None:
        """トリガーをクリア"""
        if trigger_type:
            self.triggers[trigger_type].clear()
            logger.debug(f"Cleared triggers for: {trigger_type.value}")
        else:
            for trigger_type in self.triggers:
                self.triggers[trigger_type].clear()
            self.custom_triggers.clear()
            logger.debug("Cleared all triggers")
