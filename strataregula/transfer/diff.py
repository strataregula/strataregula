"""
Diff functionality for Transfer/Copy operations

Provides change detection and visualization for copied objects.
"""

from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass
import json


class ChangeType(Enum):
    """Types of changes detected during copy operations"""
    EXCLUDED = "excluded"      # Field was excluded
    MASKED = "masked"         # Field was masked
    RENAMED = "renamed"       # Field was renamed
    MAPPED = "mapped"         # Value was mapped to different value
    COMPUTED = "computed"     # Field was computed from other fields
    DEFAULTED = "defaulted"   # Default value was added
    TYPE_CHANGED = "type_changed"  # Type conversion occurred
    MODIFIED = "modified"     # General modification


@dataclass
class FieldChange:
    """Individual field change record"""
    path: str
    change_type: ChangeType
    old_value: Any = None
    new_value: Any = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ObjectDiff:
    """Diff for a single object"""
    object_path: str
    object_meta: Dict[str, Any]
    changes: List[FieldChange]
    
    @property
    def change_count(self) -> int:
        """Total number of changes"""
        return len(self.changes)
    
    @property
    def change_types(self) -> List[ChangeType]:
        """Unique change types in this diff"""
        return list(set(change.change_type for change in self.changes))
    
    def has_change_type(self, change_type: ChangeType) -> bool:
        """Check if diff contains specific change type"""
        return change_type in self.change_types
    
    def get_changes_by_type(self, change_type: ChangeType) -> List[FieldChange]:
        """Get all changes of specific type"""
        return [change for change in self.changes if change.change_type == change_type]


class CopyDiff:
    """Diff analysis and generation for copy operations"""
    
    @staticmethod
    def create(
        original: Any, 
        copied: Any, 
        object_meta: Dict[str, Any]
    ) -> ObjectDiff:
        """
        Create diff between original and copied objects
        
        Args:
            original: Original object
            copied: Copied/transformed object  
            object_meta: Object metadata (path, kind, etc.)
            
        Returns:
            ObjectDiff with detected changes
        """
        changes = []
        object_path = object_meta.get('path', 'unknown')
        
        if isinstance(original, dict) and isinstance(copied, dict):
            changes.extend(CopyDiff._diff_dicts(original, copied, ""))
        else:
            # For non-dict objects, create simple modification record
            if original != copied:
                changes.append(FieldChange(
                    path="$",
                    change_type=ChangeType.MODIFIED,
                    old_value=original,
                    new_value=copied
                ))
        
        return ObjectDiff(
            object_path=object_path,
            object_meta=object_meta,
            changes=changes
        )
    
    @staticmethod
    def _diff_dicts(
        original: Dict[str, Any], 
        copied: Dict[str, Any], 
        path_prefix: str
    ) -> List[FieldChange]:
        """Recursively diff dictionary objects"""
        changes = []
        
        all_keys = set(original.keys()) | set(copied.keys())
        
        for key in all_keys:
            field_path = f"{path_prefix}.{key}" if path_prefix else key
            
            if key not in copied:
                # Field was excluded
                changes.append(FieldChange(
                    path=field_path,
                    change_type=ChangeType.EXCLUDED,
                    old_value=original[key],
                    new_value=None
                ))
            elif key not in original:
                # Field was added (default or computed)
                change_type = CopyDiff._infer_addition_type(copied[key])
                changes.append(FieldChange(
                    path=field_path,
                    change_type=change_type,
                    old_value=None,
                    new_value=copied[key]
                ))
            else:
                # Field exists in both, check for changes
                old_val = original[key]
                new_val = copied[key]
                
                if old_val != new_val:
                    change_type = CopyDiff._infer_change_type(old_val, new_val)
                    changes.append(FieldChange(
                        path=field_path,
                        change_type=change_type,
                        old_value=old_val,
                        new_value=new_val
                    ))
                
                # Recurse into nested dictionaries
                if isinstance(old_val, dict) and isinstance(new_val, dict):
                    changes.extend(CopyDiff._diff_dicts(old_val, new_val, field_path))
        
        return changes
    
    @staticmethod
    def _infer_change_type(old_value: Any, new_value: Any) -> ChangeType:
        """Infer change type from old and new values"""
        old_type = type(old_value)
        new_type = type(new_value)
        
        if old_type != new_type:
            return ChangeType.TYPE_CHANGED
        
        # Check for masking patterns
        if isinstance(new_value, str):
            if new_value.startswith("hash:"):
                return ChangeType.MASKED
            elif new_value == "[REDACTED]":
                return ChangeType.MASKED
            elif "*" in new_value and "*" not in str(old_value):
                return ChangeType.MASKED
        
        return ChangeType.MODIFIED
    
    @staticmethod
    def _infer_addition_type(value: Any) -> ChangeType:
        """Infer type of added field"""
        # Simple heuristics to detect computed vs default fields
        if isinstance(value, str) and value.startswith("computed_"):
            return ChangeType.COMPUTED
        
        return ChangeType.DEFAULTED
    
    @staticmethod
    def summarize(diffs: List[ObjectDiff]) -> Dict[str, Any]:
        """
        Create summary of multiple object diffs
        
        Args:
            diffs: List of ObjectDiff instances
            
        Returns:
            Summary dictionary with statistics and details
        """
        total_objects = len(diffs)
        total_changes = sum(diff.change_count for diff in diffs)
        
        # Count changes by type
        change_counts = {}
        for change_type in ChangeType:
            change_counts[change_type.value] = sum(
                len(diff.get_changes_by_type(change_type)) for diff in diffs
            )
        
        # Find objects with most changes
        most_changed = sorted(diffs, key=lambda d: d.change_count, reverse=True)[:5]
        
        # Group by change types
        objects_by_change_type = {}
        for change_type in ChangeType:
            objects_with_type = [diff for diff in diffs if diff.has_change_type(change_type)]
            objects_by_change_type[change_type.value] = len(objects_with_type)
        
        return {
            "summary": {
                "total_objects": total_objects,
                "total_changes": total_changes,
                "objects_with_changes": len([d for d in diffs if d.change_count > 0]),
                "average_changes_per_object": total_changes / max(total_objects, 1)
            },
            "change_counts": change_counts,
            "objects_by_change_type": objects_by_change_type,
            "most_changed_objects": [
                {
                    "path": diff.object_path,
                    "changes": diff.change_count,
                    "change_types": [ct.value for ct in diff.change_types]
                }
                for diff in most_changed
            ],
            "sample_changes": CopyDiff._extract_sample_changes(diffs[:10])  # First 10 objects
        }
    
    @staticmethod
    def _extract_sample_changes(diffs: List[ObjectDiff]) -> List[Dict[str, Any]]:
        """Extract sample changes for summary"""
        samples = []
        
        for diff in diffs:
            for change in diff.changes[:3]:  # Up to 3 changes per object
                sample = {
                    "object_path": diff.object_path,
                    "field_path": change.path,
                    "change_type": change.change_type.value,
                    "old_value": CopyDiff._truncate_value(change.old_value),
                    "new_value": CopyDiff._truncate_value(change.new_value)
                }
                samples.append(sample)
                
                if len(samples) >= 20:  # Limit total samples
                    break
            
            if len(samples) >= 20:
                break
        
        return samples
    
    @staticmethod
    def _truncate_value(value: Any, max_length: int = 100) -> Any:
        """Truncate long values for display"""
        if value is None:
            return None
        
        str_value = str(value)
        if len(str_value) <= max_length:
            return value
        
        return str_value[:max_length] + "..."
    
    @staticmethod
    def to_json(diff: ObjectDiff, indent: Optional[int] = 2) -> str:
        """Convert diff to JSON string"""
        data = {
            "object_path": diff.object_path,
            "object_meta": diff.object_meta,
            "change_count": diff.change_count,
            "changes": [
                {
                    "path": change.path,
                    "type": change.change_type.value,
                    "old_value": change.old_value,
                    "new_value": change.new_value,
                    "metadata": change.metadata
                }
                for change in diff.changes
            ]
        }
        
        return json.dumps(data, indent=indent, default=str)
    
    @staticmethod
    def from_json(json_str: str) -> ObjectDiff:
        """Create diff from JSON string"""
        data = json.loads(json_str)
        
        changes = []
        for change_data in data["changes"]:
            change = FieldChange(
                path=change_data["path"],
                change_type=ChangeType(change_data["type"]),
                old_value=change_data["old_value"],
                new_value=change_data["new_value"],
                metadata=change_data.get("metadata")
            )
            changes.append(change)
        
        return ObjectDiff(
            object_path=data["object_path"],
            object_meta=data["object_meta"],
            changes=changes
        )