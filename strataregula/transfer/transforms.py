"""
Transform operations for Transfer/Copy subsystem

Provides standard transformations: mask, rename, exclude, map, etc.
"""

from typing import Any, Dict, List, Optional, Callable, Union
from enum import Enum
import hashlib
import re
import logging
from abc import ABC, abstractmethod


class MaskStyle(Enum):
    """Masking styles for sensitive data"""
    STARS = "stars"        # Replace with asterisks
    HASH = "hash"          # SHA256 hash (deterministic)
    LAST4 = "last4"        # Show only last 4 characters
    REDACT = "redact"      # Replace with [REDACTED]
    NULL = "null"          # Replace with null/None


class TransformError(Exception):
    """Exceptions during transform operations"""
    pass


class Transform(ABC):
    """Base class for transform operations"""
    
    @abstractmethod
    def apply(self, obj: Any, args: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        """Apply transformation to object"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get transform name"""
        pass


class ExcludeTransform(Transform):
    """Exclude specified fields from object"""
    
    def get_name(self) -> str:
        return "exclude"
    
    def apply(self, obj: Any, args: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        if not isinstance(obj, dict):
            return obj
        
        fields = args if isinstance(args, list) else args.get('fields', [])
        result = obj.copy()
        
        for field in fields:
            result.pop(field, None)
        
        return result


class MaskTransform(Transform):
    """Mask sensitive fields with various styles"""
    
    def get_name(self) -> str:
        return "mask"
    
    def apply(self, obj: Any, args: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        if not isinstance(obj, dict):
            return obj
        
        fields = args.get('fields', [])
        style = MaskStyle(args.get('style', 'stars'))
        
        result = obj.copy()
        
        for field in fields:
            if field in result:
                result[field] = self._mask_value(result[field], style)
        
        return result
    
    def _mask_value(self, value: Any, style: MaskStyle) -> Any:
        """Apply masking to individual value"""
        if value is None:
            return value
        
        str_value = str(value)
        
        if style == MaskStyle.STARS:
            return "*" * min(len(str_value), 8)
        elif style == MaskStyle.HASH:
            return f"hash:{hashlib.sha256(str_value.encode()).hexdigest()[:16]}"
        elif style == MaskStyle.LAST4:
            if len(str_value) <= 4:
                return "*" * len(str_value)
            return "*" * (len(str_value) - 4) + str_value[-4:]
        elif style == MaskStyle.REDACT:
            return "[REDACTED]"
        elif style == MaskStyle.NULL:
            return None
        else:
            return str_value


class RenameTransform(Transform):
    """Rename fields in object"""
    
    def get_name(self) -> str:
        return "rename"
    
    def apply(self, obj: Any, args: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        if not isinstance(obj, dict):
            return obj
        
        from_field = args.get('from')
        to_field = args.get('to')
        
        if not from_field or not to_field:
            return obj
        
        result = obj.copy()
        
        if from_field in result:
            # Support nested field names like "profile.address"
            if '.' in to_field:
                result = self._set_nested(result, to_field, result.pop(from_field))
            else:
                result[to_field] = result.pop(from_field)
        
        return result
    
    def _set_nested(self, obj: Dict, path: str, value: Any) -> Dict:
        """Set nested field using dot notation"""
        keys = path.split('.')
        current = obj
        
        # Create nested structure if needed
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        return obj


class MapTransform(Transform):
    """Map values using lookup table"""
    
    def get_name(self) -> str:
        return "map"
    
    def apply(self, obj: Any, args: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        if not isinstance(obj, dict):
            return obj
        
        field = args.get('field')
        mapping = args.get('mapping', {})
        default = args.get('default')
        
        if not field or not mapping:
            return obj
        
        result = obj.copy()
        
        if field in result:
            old_value = result[field]
            new_value = mapping.get(old_value, default if default is not None else old_value)
            result[field] = new_value
        
        return result


class DefaultTransform(Transform):
    """Set default values for missing fields"""
    
    def get_name(self) -> str:
        return "default"
    
    def apply(self, obj: Any, args: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        if not isinstance(obj, dict):
            return obj
        
        defaults = args.get('values', {})
        
        result = obj.copy()
        
        for field, default_value in defaults.items():
            if field not in result or result[field] is None:
                result[field] = default_value
        
        return result


class ComputeTransform(Transform):
    """Compute new fields from existing data"""
    
    def get_name(self) -> str:
        return "compute"
    
    def apply(self, obj: Any, args: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        if not isinstance(obj, dict):
            return obj
        
        field = args.get('field')
        expression = args.get('expression')
        
        if not field or not expression:
            return obj
        
        result = obj.copy()
        
        # Simple expression evaluation (security consideration: limit to safe operations)
        try:
            # TODO: Implement safe expression evaluator
            # For now, support basic string operations
            if expression == "uppercase":
                source_field = args.get('source', field)
                if source_field in result:
                    result[field] = str(result[source_field]).upper()
            elif expression == "lowercase":
                source_field = args.get('source', field)
                if source_field in result:
                    result[field] = str(result[source_field]).lower()
            elif expression == "length":
                source_field = args.get('source', field)
                if source_field in result:
                    result[field] = len(str(result[source_field]))
            # Add more safe expressions as needed
        except Exception as e:
            logging.warning(f"Compute transform failed for field '{field}': {e}")
        
        return result


class IdReassignTransform(Transform):
    """Reassign IDs with prefix/suffix"""
    
    def get_name(self) -> str:
        return "id_reassign"
    
    def apply(self, obj: Any, args: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        if not isinstance(obj, dict):
            return obj
        
        field = args.get('field', 'id')
        prefix = args.get('prefix', '')
        suffix = args.get('suffix', '')
        
        result = obj.copy()
        
        if field in result:
            old_id = str(result[field])
            new_id = f"{prefix}{old_id}{suffix}"
            result[field] = new_id
        
        return result


class ArrayMergeTransform(Transform):
    """Merge arrays with various strategies"""
    
    def get_name(self) -> str:
        return "array_merge"
    
    def apply(self, obj: Any, args: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        # TODO: Implement array merging strategies
        # - append: add to end
        # - prepend: add to beginning  
        # - unique-by: merge removing duplicates by key
        # - replace: replace entire array
        return obj


class TransformRegistry:
    """Registry of available transforms"""
    
    def __init__(self):
        self.transforms: Dict[str, Transform] = {}
        self.logger = logging.getLogger(__name__)
        
        # Register standard transforms
        self._register_standard_transforms()
    
    def _register_standard_transforms(self):
        """Register built-in transforms"""
        standard_transforms = [
            ExcludeTransform(),
            MaskTransform(),
            RenameTransform(),
            MapTransform(),
            DefaultTransform(),
            ComputeTransform(),
            IdReassignTransform(),
            ArrayMergeTransform()
        ]
        
        for transform in standard_transforms:
            self.register(transform.get_name(), transform)
    
    def register(self, name: str, transform: Transform):
        """Register a transform"""
        self.transforms[name] = transform
    
    def unregister(self, name: str) -> bool:
        """Unregister a transform"""
        return self.transforms.pop(name, None) is not None
    
    def get_transform(self, name: str) -> Optional[Transform]:
        """Get transform by name"""
        return self.transforms.get(name)
    
    def list_transforms(self) -> List[str]:
        """List available transform names"""
        return list(self.transforms.keys())
    
    def apply(self, obj: Any, op: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        """
        Apply transform operation to object
        
        Args:
            obj: Object to transform
            op: Operation specification (e.g., {"exclude": ["password"]})
            meta: Object metadata
            
        Returns:
            Transformed object
        """
        if not isinstance(op, dict) or len(op) != 1:
            raise TransformError(f"Invalid operation format: {op}")
        
        op_name, op_args = next(iter(op.items()))
        
        transform = self.get_transform(op_name)
        if not transform:
            raise TransformError(f"Unknown transform: {op_name}")
        
        try:
            return transform.apply(obj, op_args, meta)
        except Exception as e:
            self.logger.error(f"Transform '{op_name}' failed: {e}")
            raise TransformError(f"Transform '{op_name}' failed: {e}")
    
    def validate_operation(self, op: Dict[str, Any]) -> List[str]:
        """Validate operation syntax"""
        issues = []
        
        if not isinstance(op, dict):
            issues.append("Operation must be a dictionary")
            return issues
        
        if len(op) != 1:
            issues.append("Operation must have exactly one transform")
            return issues
        
        op_name, op_args = next(iter(op.items()))
        
        if op_name not in self.transforms:
            issues.append(f"Unknown transform: {op_name}")
        
        # TODO: Add specific validation for each transform type
        
        return issues