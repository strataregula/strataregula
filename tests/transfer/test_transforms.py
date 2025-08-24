"""
Unit tests for Transform operations

Tests for mask, rename, exclude, and other transform operations.
"""

import pytest
from strataregula.transfer.transforms import (
    TransformRegistry, TransformError, MaskStyle,
    ExcludeTransform, MaskTransform, RenameTransform,
    MapTransform, DefaultTransform, ComputeTransform, IdReassignTransform
)


class TestTransformRegistry:
    """Test TransformRegistry functionality"""
    
    def test_registry_initialization(self):
        """Test registry creates with standard transforms"""
        registry = TransformRegistry()
        
        standard_transforms = [
            'exclude', 'mask', 'rename', 'map', 
            'default', 'compute', 'id_reassign', 'array_merge'
        ]
        
        available = registry.list_transforms()
        for transform_name in standard_transforms:
            assert transform_name in available
    
    def test_apply_valid_operation(self, sample_user_data):
        """Test applying valid transformation"""
        registry = TransformRegistry()
        user = sample_user_data["users"][0]
        
        result = registry.apply(
            user, 
            {"exclude": ["password"]}, 
            {"path": "$.users[0]"}
        )
        
        assert "password" not in result
        assert "name" in result
        assert result["name"] == user["name"]
    
    def test_apply_invalid_operation(self, sample_user_data):
        """Test applying invalid transformation"""
        registry = TransformRegistry()
        user = sample_user_data["users"][0]
        
        with pytest.raises(TransformError):
            registry.apply(user, {"nonexistent": []}, {})
    
    def test_apply_malformed_operation(self, sample_user_data):
        """Test applying malformed transformation"""
        registry = TransformRegistry()
        user = sample_user_data["users"][0]
        
        # Multiple operations in one dict (invalid)
        with pytest.raises(TransformError):
            registry.apply(user, {"exclude": [], "mask": []}, {})
        
        # Non-dict operation (invalid)
        with pytest.raises(TransformError):
            registry.apply(user, "invalid", {})
    
    def test_register_custom_transform(self):
        """Test registering custom transform"""
        registry = TransformRegistry()
        
        class CustomTransform:
            def get_name(self):
                return "custom"
            
            def apply(self, obj, args, meta):
                return {"custom": True}
        
        custom = CustomTransform()
        registry.register("custom", custom)
        
        assert "custom" in registry.list_transforms()
        assert registry.get_transform("custom") is custom


class TestExcludeTransform:
    """Test exclude transformation"""
    
    def test_exclude_single_field(self, sample_user_data):
        """Test excluding single field"""
        transform = ExcludeTransform()
        user = sample_user_data["users"][0].copy()
        
        result = transform.apply(user, ["password"], {})
        
        assert "password" not in result
        assert "name" in result
        assert "email" in result
    
    def test_exclude_multiple_fields(self, sample_user_data):
        """Test excluding multiple fields"""
        transform = ExcludeTransform()
        user = sample_user_data["users"][0].copy()
        
        result = transform.apply(user, ["password", "email"], {})
        
        assert "password" not in result
        assert "email" not in result
        assert "name" in result
    
    def test_exclude_nonexistent_field(self, sample_user_data):
        """Test excluding nonexistent field"""
        transform = ExcludeTransform()
        user = sample_user_data["users"][0].copy()
        
        result = transform.apply(user, ["nonexistent"], {})
        
        assert result == user  # No change
    
    def test_exclude_with_dict_args(self, sample_user_data):
        """Test exclude with dictionary arguments"""
        transform = ExcludeTransform()
        user = sample_user_data["users"][0].copy()
        
        result = transform.apply(user, {"fields": ["password"]}, {})
        
        assert "password" not in result
    
    def test_exclude_non_dict_object(self):
        """Test exclude on non-dictionary object"""
        transform = ExcludeTransform()
        
        result = transform.apply("string", ["anything"], {})
        assert result == "string"  # No change for non-dict


class TestMaskTransform:
    """Test mask transformation"""
    
    def test_mask_with_stars(self, sample_user_data):
        """Test masking with stars"""
        transform = MaskTransform()
        user = sample_user_data["users"][0].copy()
        
        result = transform.apply(
            user,
            {"fields": ["password"], "style": "stars"},
            {}
        )
        
        assert result["password"] == "********"  # Stars mask
        assert result["name"] == user["name"]  # Other fields unchanged
    
    def test_mask_with_hash(self, sample_user_data):
        """Test masking with hash"""
        transform = MaskTransform()
        user = sample_user_data["users"][0].copy()
        
        result = transform.apply(
            user,
            {"fields": ["email"], "style": "hash"},
            {}
        )
        
        assert result["email"].startswith("hash:")
        assert len(result["email"]) > 5  # hash: + hex digits
    
    def test_mask_with_last4(self, sample_user_data):
        """Test masking with last4"""
        transform = MaskTransform()
        user = sample_user_data["users"][0].copy()
        
        result = transform.apply(
            user,
            {"fields": ["email"], "style": "last4"},
            {}
        )
        
        original_email = user["email"]
        expected = "*" * (len(original_email) - 4) + original_email[-4:]
        assert result["email"] == expected
    
    def test_mask_with_redact(self, sample_user_data):
        """Test masking with redaction"""
        transform = MaskTransform()
        user = sample_user_data["users"][0].copy()
        
        result = transform.apply(
            user,
            {"fields": ["password"], "style": "redact"},
            {}
        )
        
        assert result["password"] == "[REDACTED]"
    
    def test_mask_with_null(self, sample_user_data):
        """Test masking with null"""
        transform = MaskTransform()
        user = sample_user_data["users"][0].copy()
        
        result = transform.apply(
            user,
            {"fields": ["password"], "style": "null"},
            {}
        )
        
        assert result["password"] is None
    
    def test_mask_multiple_fields(self, sample_user_data):
        """Test masking multiple fields"""
        transform = MaskTransform()
        user = sample_user_data["users"][0].copy()
        
        result = transform.apply(
            user,
            {"fields": ["password", "email"], "style": "stars"},
            {}
        )
        
        assert result["password"] == "********"
        assert result["email"] == "********"
    
    def test_mask_nonexistent_field(self, sample_user_data):
        """Test masking nonexistent field"""
        transform = MaskTransform()
        user = sample_user_data["users"][0].copy()
        
        result = transform.apply(
            user,
            {"fields": ["nonexistent"], "style": "stars"},
            {}
        )
        
        assert result == user  # No change
    
    def test_mask_none_value(self):
        """Test masking None values"""
        transform = MaskTransform()
        data = {"field": None}
        
        result = transform.apply(
            data,
            {"fields": ["field"], "style": "stars"},
            {}
        )
        
        assert result["field"] is None  # None should remain None


class TestRenameTransform:
    """Test rename transformation"""
    
    def test_rename_simple_field(self, sample_user_data):
        """Test renaming simple field"""
        transform = RenameTransform()
        user = sample_user_data["users"][0].copy()
        
        result = transform.apply(
            user,
            {"from": "name", "to": "full_name"},
            {}
        )
        
        assert "name" not in result
        assert "full_name" in result
        assert result["full_name"] == user["name"]
    
    def test_rename_to_nested_field(self, sample_user_data):
        """Test renaming to nested field"""
        transform = RenameTransform()
        user = sample_user_data["users"][0].copy()
        
        result = transform.apply(
            user,
            {"from": "email", "to": "contact.email"},
            {}
        )
        
        assert "email" not in result
        assert "contact" in result
        assert result["contact"]["email"] == user["email"]
    
    def test_rename_nonexistent_field(self, sample_user_data):
        """Test renaming nonexistent field"""
        transform = RenameTransform()
        user = sample_user_data["users"][0].copy()
        
        result = transform.apply(
            user,
            {"from": "nonexistent", "to": "new_field"},
            {}
        )
        
        assert result == user  # No change
    
    def test_rename_missing_args(self, sample_user_data):
        """Test rename with missing arguments"""
        transform = RenameTransform()
        user = sample_user_data["users"][0].copy()
        
        # Missing 'to' argument
        result = transform.apply(user, {"from": "name"}, {})
        assert result == user
        
        # Missing 'from' argument
        result = transform.apply(user, {"to": "new_name"}, {})
        assert result == user


class TestMapTransform:
    """Test map transformation"""
    
    def test_map_simple_value(self):
        """Test mapping simple value"""
        transform = MapTransform()
        data = {"status": "active"}
        
        mapping = {"active": "enabled", "inactive": "disabled"}
        result = transform.apply(
            data,
            {"field": "status", "mapping": mapping},
            {}
        )
        
        assert result["status"] == "enabled"
    
    def test_map_with_default(self):
        """Test mapping with default value"""
        transform = MapTransform()
        data = {"status": "unknown"}
        
        mapping = {"active": "enabled", "inactive": "disabled"}
        result = transform.apply(
            data,
            {"field": "status", "mapping": mapping, "default": "pending"},
            {}
        )
        
        assert result["status"] == "pending"
    
    def test_map_without_default(self):
        """Test mapping without default (keeps original)"""
        transform = MapTransform()
        data = {"status": "unknown"}
        
        mapping = {"active": "enabled", "inactive": "disabled"}
        result = transform.apply(
            data,
            {"field": "status", "mapping": mapping},
            {}
        )
        
        assert result["status"] == "unknown"  # Original value preserved


class TestDefaultTransform:
    """Test default transformation"""
    
    def test_set_default_for_missing_field(self):
        """Test setting default for missing field"""
        transform = DefaultTransform()
        data = {"name": "Alice"}
        
        result = transform.apply(
            data,
            {"values": {"status": "active", "role": "user"}},
            {}
        )
        
        assert result["name"] == "Alice"  # Original field preserved
        assert result["status"] == "active"  # Default added
        assert result["role"] == "user"  # Default added
    
    def test_set_default_for_null_field(self):
        """Test setting default for null field"""
        transform = DefaultTransform()
        data = {"name": "Alice", "status": None}
        
        result = transform.apply(
            data,
            {"values": {"status": "active"}},
            {}
        )
        
        assert result["status"] == "active"  # Default replaces null
    
    def test_keep_existing_values(self):
        """Test keeping existing non-null values"""
        transform = DefaultTransform()
        data = {"name": "Alice", "status": "inactive"}
        
        result = transform.apply(
            data,
            {"values": {"status": "active", "role": "user"}},
            {}
        )
        
        assert result["status"] == "inactive"  # Existing value kept
        assert result["role"] == "user"  # Default added for missing field


class TestComputeTransform:
    """Test compute transformation"""
    
    def test_compute_uppercase(self):
        """Test compute uppercase transformation"""
        transform = ComputeTransform()
        data = {"name": "alice"}
        
        result = transform.apply(
            data,
            {"field": "name_upper", "expression": "uppercase", "source": "name"},
            {}
        )
        
        assert result["name_upper"] == "ALICE"
        assert result["name"] == "alice"  # Original preserved
    
    def test_compute_lowercase(self):
        """Test compute lowercase transformation"""
        transform = ComputeTransform()
        data = {"name": "ALICE"}
        
        result = transform.apply(
            data,
            {"field": "name_lower", "expression": "lowercase", "source": "name"},
            {}
        )
        
        assert result["name_lower"] == "alice"
    
    def test_compute_length(self):
        """Test compute length transformation"""
        transform = ComputeTransform()
        data = {"email": "alice@example.com"}
        
        result = transform.apply(
            data,
            {"field": "email_length", "expression": "length", "source": "email"},
            {}
        )
        
        assert result["email_length"] == len("alice@example.com")
    
    def test_compute_missing_source_field(self):
        """Test compute with missing source field"""
        transform = ComputeTransform()
        data = {"name": "alice"}
        
        result = transform.apply(
            data,
            {"field": "computed", "expression": "uppercase", "source": "nonexistent"},
            {}
        )
        
        # Should not add the computed field if source is missing
        assert "computed" not in result
        assert result == data


class TestIdReassignTransform:
    """Test ID reassignment transformation"""
    
    def test_reassign_with_prefix(self):
        """Test ID reassignment with prefix"""
        transform = IdReassignTransform()
        data = {"id": "12345"}
        
        result = transform.apply(
            data,
            {"prefix": "dev_"},
            {}
        )
        
        assert result["id"] == "dev_12345"
    
    def test_reassign_with_suffix(self):
        """Test ID reassignment with suffix"""
        transform = IdReassignTransform()
        data = {"id": "12345"}
        
        result = transform.apply(
            data,
            {"suffix": "_test"},
            {}
        )
        
        assert result["id"] == "12345_test"
    
    def test_reassign_with_prefix_and_suffix(self):
        """Test ID reassignment with both prefix and suffix"""
        transform = IdReassignTransform()
        data = {"id": "12345"}
        
        result = transform.apply(
            data,
            {"prefix": "dev_", "suffix": "_test"},
            {}
        )
        
        assert result["id"] == "dev_12345_test"
    
    def test_reassign_custom_field(self):
        """Test ID reassignment on custom field"""
        transform = IdReassignTransform()
        data = {"user_id": "alice"}
        
        result = transform.apply(
            data,
            {"field": "user_id", "prefix": "usr_"},
            {}
        )
        
        assert result["user_id"] == "usr_alice"
    
    def test_reassign_missing_field(self):
        """Test ID reassignment on missing field"""
        transform = IdReassignTransform()
        data = {"name": "alice"}
        
        result = transform.apply(
            data,
            {"prefix": "dev_"},
            {}
        )
        
        assert result == data  # No change if field missing


class TestTransformChaining:
    """Test chaining multiple transforms"""
    
    def test_chain_exclude_and_mask(self, sample_user_data):
        """Test chaining exclude and mask transforms"""
        registry = TransformRegistry()
        user = sample_user_data["users"][0].copy()
        
        # First exclude password
        result = registry.apply(user, {"exclude": ["password"]}, {})
        
        # Then mask email
        result = registry.apply(result, {"mask": {"fields": ["email"], "style": "hash"}}, {})
        
        assert "password" not in result
        assert result["email"].startswith("hash:")
        assert result["name"] == user["name"]
    
    def test_chain_rename_and_compute(self, sample_user_data):
        """Test chaining rename and compute transforms"""
        registry = TransformRegistry()
        user = sample_user_data["users"][0].copy()
        
        # First rename
        result = registry.apply(user, {"rename": {"from": "name", "to": "full_name"}}, {})
        
        # Then compute uppercase
        result = registry.apply(
            result,
            {"compute": {"field": "name_upper", "expression": "uppercase", "source": "full_name"}},
            {}
        )
        
        assert "name" not in result
        assert result["full_name"] == user["name"]
        assert result["name_upper"] == user["name"].upper()