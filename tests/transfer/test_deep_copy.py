"""
Unit tests for DeepCopyVisitor

Tests for safe copying with circular reference detection,
depth limiting, and type restrictions.
"""

import pytest
from strataregula.transfer.deep_copy import (
    DeepCopyVisitor, CopyMode, CopyError, 
    CircularReferenceError, DepthLimitError, TypeRestrictError,
    safe_deep_copy, copy_with_limits
)


class TestDeepCopyVisitor:
    """Test DeepCopyVisitor functionality"""
    
    def test_shallow_copy_basic(self):
        """Test basic shallow copy functionality"""
        visitor = DeepCopyVisitor()
        original = {"a": 1, "b": [1, 2, 3], "c": {"nested": "value"}}
        
        result = visitor.copy(original, CopyMode.SHALLOW)
        
        assert result == original
        assert result is not original  # Different object
        assert result["c"] is original["c"]  # Shallow - nested objects are shared
    
    def test_deep_copy_basic(self):
        """Test basic deep copy functionality"""
        visitor = DeepCopyVisitor()
        original = {"a": 1, "b": [1, 2, 3], "c": {"nested": "value"}}
        
        result = visitor.copy(original, CopyMode.DEEP)
        
        assert result == original
        assert result is not original  # Different object
        assert result["c"] is not original["c"]  # Deep - nested objects are copied
    
    def test_link_copy(self):
        """Test link copy (reference sharing)"""
        visitor = DeepCopyVisitor()
        original = {"a": 1, "b": [1, 2, 3]}
        
        result = visitor.copy(original, CopyMode.LINK)
        
        assert result is original  # Same object reference
    
    def test_circular_reference_detection(self, circular_reference_data):
        """Test circular reference detection"""
        visitor = DeepCopyVisitor()
        
        with pytest.raises(CircularReferenceError) as exc_info:
            visitor.copy(circular_reference_data, CopyMode.DEEP)
        
        assert "Circular reference detected" in str(exc_info.value)
    
    def test_depth_limit(self, deep_nested_data):
        """Test maximum depth limiting"""
        visitor = DeepCopyVisitor(max_depth=10)
        
        with pytest.raises(DepthLimitError) as exc_info:
            visitor.copy(deep_nested_data, CopyMode.DEEP)
        
        assert "Maximum copy depth 10 exceeded" in str(exc_info.value)
    
    def test_depth_limit_success(self):
        """Test deep copy within depth limit"""
        visitor = DeepCopyVisitor(max_depth=5)
        
        # Create nested data within limit
        data = {"level1": {"level2": {"level3": {"value": "deep"}}}}
        
        result = visitor.copy(data, CopyMode.DEEP)
        assert result == data
        assert result is not data
    
    def test_type_restrictions(self):
        """Test type restriction enforcement"""
        # Allow only basic types
        visitor = DeepCopyVisitor(allowed_types=(dict, list, str, int))
        
        # This should work
        valid_data = {"name": "test", "numbers": [1, 2, 3]}
        result = visitor.copy(valid_data, CopyMode.DEEP)
        assert result == valid_data
        
        # This should fail due to float not being allowed
        invalid_data = {"value": 3.14}
        with pytest.raises(TypeRestrictError):
            visitor.copy(invalid_data, CopyMode.DEEP)
    
    def test_max_keys_limit(self):
        """Test maximum keys limit"""
        visitor = DeepCopyVisitor(max_keys=5)
        
        # This should work
        small_dict = {f"key_{i}": i for i in range(3)}
        result = visitor.copy(small_dict, CopyMode.DEEP)
        assert result == small_dict
        
        # This should fail
        large_dict = {f"key_{i}": i for i in range(100)}
        with pytest.raises(TypeRestrictError) as exc_info:
            visitor.copy(large_dict, CopyMode.DEEP)
        
        assert "Dictionary too large" in str(exc_info.value)
    
    def test_max_array_size_limit(self):
        """Test maximum array size limit"""
        visitor = DeepCopyVisitor(max_array_size=10)
        
        # This should work
        small_list = list(range(5))
        result = visitor.copy(small_list, CopyMode.DEEP)
        assert result == small_list
        
        # This should fail
        large_list = list(range(100))
        with pytest.raises(TypeRestrictError) as exc_info:
            visitor.copy(large_list, CopyMode.DEEP)
        
        assert "List too large" in str(exc_info.value)
    
    def test_primitive_types(self):
        """Test copying of primitive types"""
        visitor = DeepCopyVisitor()
        
        primitives = [
            None, True, False, 42, 3.14, "hello", b"bytes"
        ]
        
        for primitive in primitives:
            result = visitor.copy(primitive, CopyMode.DEEP)
            assert result == primitive
            assert result is primitive  # Primitives should be the same object
    
    def test_complex_nested_structure(self, sample_user_data):
        """Test copying complex nested structures"""
        visitor = DeepCopyVisitor()
        
        result = visitor.copy(sample_user_data, CopyMode.DEEP)
        
        assert result == sample_user_data
        assert result is not sample_user_data
        assert result["users"][0] is not sample_user_data["users"][0]
        assert result["users"][0]["profile"] is not sample_user_data["users"][0]["profile"]
    
    def test_estimate_copy_cost(self, sample_user_data):
        """Test copy cost estimation"""
        visitor = DeepCopyVisitor()
        
        # Deep copy estimation
        deep_stats = visitor.estimate_copy_cost(sample_user_data, CopyMode.DEEP)
        assert deep_stats["objects"] > 0
        assert deep_stats["primitives"] > 0
        assert deep_stats["max_depth"] > 0
        assert deep_stats["estimated_memory"] > 0
        
        # Shallow copy should be cheaper
        shallow_stats = visitor.estimate_copy_cost(sample_user_data, CopyMode.SHALLOW)
        assert shallow_stats["estimated_memory"] < deep_stats["estimated_memory"]
        
        # Link copy should be minimal
        link_stats = visitor.estimate_copy_cost(sample_user_data, CopyMode.LINK)
        assert link_stats["estimated_memory"] == 0


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_safe_deep_copy(self, sample_user_data):
        """Test safe_deep_copy convenience function"""
        result = safe_deep_copy(sample_user_data)
        
        assert result == sample_user_data
        assert result is not sample_user_data
    
    def test_safe_deep_copy_with_limits(self, deep_nested_data):
        """Test safe_deep_copy with custom limits"""
        with pytest.raises(DepthLimitError):
            safe_deep_copy(deep_nested_data, max_depth=10)
    
    def test_copy_with_limits(self, sample_user_data):
        """Test copy_with_limits convenience function"""
        result = copy_with_limits(
            sample_user_data,
            mode=CopyMode.SHALLOW,
            max_depth=5,
            max_keys=100
        )
        
        assert result == sample_user_data
        assert result is not sample_user_data
    
    def test_copy_with_limits_failure(self, large_array_data):
        """Test copy_with_limits with exceeded limits"""
        with pytest.raises(TypeRestrictError):
            copy_with_limits(
                large_array_data,
                mode=CopyMode.DEEP,
                max_array_size=100
            )


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_structures(self):
        """Test copying empty structures"""
        visitor = DeepCopyVisitor()
        
        empty_dict = {}
        empty_list = []
        empty_set = set()
        
        assert visitor.copy(empty_dict, CopyMode.DEEP) == {}
        assert visitor.copy(empty_list, CopyMode.DEEP) == []
        assert visitor.copy(empty_set, CopyMode.DEEP) == set()
    
    def test_mixed_types(self):
        """Test copying mixed data types"""
        visitor = DeepCopyVisitor()
        
        mixed_data = {
            "dict": {"nested": "value"},
            "list": [1, 2, {"inner": "list"}],
            "tuple": (1, 2, 3),
            "set": {1, 2, 3},
            "frozenset": frozenset([4, 5, 6])
        }
        
        result = visitor.copy(mixed_data, CopyMode.DEEP)
        
        assert result == mixed_data
        assert result is not mixed_data
        assert isinstance(result["tuple"], tuple)
        assert isinstance(result["set"], set)
        assert isinstance(result["frozenset"], frozenset)
    
    def test_self_reference(self):
        """Test object that references itself"""
        visitor = DeepCopyVisitor()
        
        data = {"name": "self"}
        data["self"] = data  # Self-reference
        
        with pytest.raises(CircularReferenceError):
            visitor.copy(data, CopyMode.DEEP)
    
    def test_complex_circular_reference(self):
        """Test complex circular reference patterns"""
        visitor = DeepCopyVisitor()
        
        # A -> B -> C -> A cycle
        a = {"name": "a"}
        b = {"name": "b"}
        c = {"name": "c"}
        
        a["next"] = b
        b["next"] = c
        c["next"] = a  # Creates cycle
        
        root = {"start": a}
        
        with pytest.raises(CircularReferenceError):
            visitor.copy(root, CopyMode.DEEP)