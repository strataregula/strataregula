"""
Deep Copy Visitor with safety features

Provides safe copying with circular reference detection, depth limiting,
and type restrictions.
"""

from typing import Any, Dict, List, Set, Type, Union
from enum import Enum
import copy
import logging
from weakref import WeakSet


class CopyMode(Enum):
    """Copy modes for different use cases"""
    DEEP = "deep"          # Complete recursive copy with safety checks
    SHALLOW = "shallow"    # One-level copy only
    LINK = "link"          # Reference sharing (read-only)
    COW = "cow"           # Copy-on-write proxy


class CopyError(Exception):
    """Exceptions during copy operations"""
    pass


class CircularReferenceError(CopyError):
    """Circular reference detected during copy"""
    pass


class DepthLimitError(CopyError):
    """Maximum copy depth exceeded"""
    pass


class TypeRestrictError(CopyError):
    """Unsupported type encountered"""
    pass


class DeepCopyVisitor:
    """
    Safe deep copy implementation with configurable safety limits
    """
    
    DEFAULT_MAX_DEPTH = 64
    DEFAULT_ALLOWED_TYPES = (
        dict, list, tuple, set, frozenset,
        str, int, float, bool, bytes,
        type(None)
    )
    
    def __init__(
        self,
        max_depth: int = DEFAULT_MAX_DEPTH,
        allowed_types: tuple = DEFAULT_ALLOWED_TYPES,
        max_keys: int = 10000,
        max_array_size: int = 100000
    ):
        self.max_depth = max_depth
        self.allowed_types = allowed_types
        self.max_keys = max_keys
        self.max_array_size = max_array_size
        self.logger = logging.getLogger(__name__)
    
    def copy(self, value: Any, mode: CopyMode = CopyMode.DEEP) -> Any:
        """
        Copy value according to specified mode
        
        Args:
            value: Object to copy
            mode: Copy mode to use
            
        Returns:
            Copied object
            
        Raises:
            CircularReferenceError: If circular reference detected
            DepthLimitError: If max depth exceeded
            TypeRestrictError: If unsupported type encountered
        """
        if mode == CopyMode.SHALLOW:
            return self._shallow_copy(value)
        elif mode == CopyMode.LINK:
            return value  # Return reference as-is
        elif mode == CopyMode.COW:
            return self._copy_on_write_proxy(value)
        else:  # CopyMode.DEEP
            return self._deep_copy(value)
    
    def _shallow_copy(self, value: Any) -> Any:
        """Perform shallow copy with type checking"""
        self._check_type(value)
        
        if isinstance(value, dict):
            if len(value) > self.max_keys:
                raise TypeRestrictError(f"Dictionary too large: {len(value)} > {self.max_keys}")
            return dict(value)
        elif isinstance(value, (list, tuple)):
            if len(value) > self.max_array_size:
                raise TypeRestrictError(f"Array too large: {len(value)} > {self.max_array_size}")
            return type(value)(value)
        elif isinstance(value, set):
            return set(value)
        else:
            return copy.copy(value)
    
    def _deep_copy(self, value: Any) -> Any:
        """Perform deep copy with safety checks"""
        visited_ids: Set[int] = set()
        return self._deep_copy_recursive(value, visited_ids, 0)
    
    def _deep_copy_recursive(self, value: Any, visited_ids: Set[int], depth: int) -> Any:
        """Recursive deep copy with safety tracking"""
        # Depth check
        if depth > self.max_depth:
            raise DepthLimitError(f"Maximum copy depth {self.max_depth} exceeded")
        
        # Type check
        self._check_type(value)
        
        # Handle immutable/primitive types
        if value is None or isinstance(value, (str, int, float, bool, bytes)):
            return value
        
        # Circular reference check
        obj_id = id(value)
        if obj_id in visited_ids:
            raise CircularReferenceError(f"Circular reference detected at depth {depth}")
        
        # Add to visited set
        visited_ids.add(obj_id)
        
        try:
            if isinstance(value, dict):
                if len(value) > self.max_keys:
                    raise TypeRestrictError(f"Dictionary too large: {len(value)} > {self.max_keys}")
                
                result = {}
                for k, v in value.items():
                    new_key = self._deep_copy_recursive(k, visited_ids, depth + 1)
                    new_value = self._deep_copy_recursive(v, visited_ids, depth + 1)
                    result[new_key] = new_value
                return result
                
            elif isinstance(value, list):
                if len(value) > self.max_array_size:
                    raise TypeRestrictError(f"List too large: {len(value)} > {self.max_array_size}")
                
                return [self._deep_copy_recursive(item, visited_ids, depth + 1) for item in value]
                
            elif isinstance(value, tuple):
                if len(value) > self.max_array_size:
                    raise TypeRestrictError(f"Tuple too large: {len(value)} > {self.max_array_size}")
                
                return tuple(self._deep_copy_recursive(item, visited_ids, depth + 1) for item in value)
                
            elif isinstance(value, set):
                return {self._deep_copy_recursive(item, visited_ids, depth + 1) for item in value}
                
            elif isinstance(value, frozenset):
                return frozenset(self._deep_copy_recursive(item, visited_ids, depth + 1) for item in value)
                
            else:
                # Fallback to standard copy for other types
                return copy.deepcopy(value)
                
        finally:
            # Remove from visited set when backtracking
            visited_ids.discard(obj_id)
    
    def _check_type(self, value: Any) -> None:
        """Check if type is allowed"""
        if not isinstance(value, self.allowed_types):
            raise TypeRestrictError(f"Type {type(value).__name__} not allowed")
    
    def _copy_on_write_proxy(self, value: Any) -> Any:
        """
        Create copy-on-write proxy (simplified implementation)
        
        Note: This is a placeholder. Full COW implementation would require
        proxy objects that defer copying until modification.
        """
        # For now, just return a shallow copy
        # TODO: Implement proper COW proxy objects
        return self._shallow_copy(value)
    
    def estimate_copy_cost(self, value: Any, mode: CopyMode = CopyMode.DEEP) -> Dict[str, int]:
        """
        Estimate cost of copying operation
        
        Args:
            value: Object to analyze
            mode: Copy mode
            
        Returns:
            Dictionary with cost estimates
        """
        stats = {
            "objects": 0,
            "primitives": 0,
            "max_depth": 0,
            "estimated_memory": 0,
            "estimated_time_ms": 0
        }
        
        if mode == CopyMode.LINK:
            return stats
        
        self._analyze_recursive(value, stats, set(), 0)
        
        # Estimate memory (rough approximation)
        if mode == CopyMode.DEEP:
            stats["estimated_memory"] = stats["objects"] * 100 + stats["primitives"] * 50
        else:  # SHALLOW or COW
            stats["estimated_memory"] = stats["objects"] * 50 + stats["primitives"] * 10
        
        # Estimate time (very rough - 1μs per object/primitive)
        stats["estimated_time_ms"] = (stats["objects"] + stats["primitives"]) * 0.001
        
        return stats
    
    def _analyze_recursive(self, value: Any, stats: Dict[str, int], visited: Set[int], depth: int) -> None:
        """Recursively analyze object structure for cost estimation"""
        if depth > self.max_depth:
            return
        
        stats["max_depth"] = max(stats["max_depth"], depth)
        
        if value is None or isinstance(value, (str, int, float, bool, bytes)):
            stats["primitives"] += 1
            return
        
        obj_id = id(value)
        if obj_id in visited:
            return
        
        visited.add(obj_id)
        stats["objects"] += 1
        
        try:
            if isinstance(value, dict):
                for k, v in value.items():
                    self._analyze_recursive(k, stats, visited, depth + 1)
                    self._analyze_recursive(v, stats, visited, depth + 1)
            elif isinstance(value, (list, tuple, set, frozenset)):
                for item in value:
                    self._analyze_recursive(item, stats, visited, depth + 1)
        finally:
            visited.discard(obj_id)


# Utility functions
def safe_deep_copy(
    obj: Any, 
    max_depth: int = 64, 
    allowed_types: tuple = None
) -> Any:
    """Convenience function for safe deep copying"""
    visitor = DeepCopyVisitor(
        max_depth=max_depth,
        allowed_types=allowed_types or DeepCopyVisitor.DEFAULT_ALLOWED_TYPES
    )
    return visitor.copy(obj, CopyMode.DEEP)


def copy_with_limits(
    obj: Any,
    mode: CopyMode = CopyMode.DEEP,
    max_depth: int = 64,
    max_keys: int = 10000,
    max_array_size: int = 100000
) -> Any:
    """Convenience function for copy with custom limits"""
    visitor = DeepCopyVisitor(
        max_depth=max_depth,
        max_keys=max_keys,
        max_array_size=max_array_size
    )
    return visitor.copy(obj, mode)