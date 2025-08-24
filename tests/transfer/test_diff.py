"""
Unit tests for Diff functionality

Tests for change detection and visualization for copied objects.
"""

import pytest
from strataregula.transfer.diff import (
    CopyDiff, ObjectDiff, FieldChange, ChangeType
)


class TestFieldChange:
    """Test FieldChange functionality"""
    
    def test_field_change_creation(self):
        """Test creating field change record"""
        change = FieldChange(
            path="$.email",
            change_type=ChangeType.MASKED,
            old_value="alice@example.com",
            new_value="hash:abc123"
        )
        
        assert change.path == "$.email"
        assert change.change_type == ChangeType.MASKED
        assert change.old_value == "alice@example.com"
        assert change.new_value == "hash:abc123"
    
    def test_field_change_with_metadata(self):
        """Test field change with metadata"""
        change = FieldChange(
            path="$.id",
            change_type=ChangeType.MODIFIED,
            old_value="123",
            new_value="dev_123",
            metadata={"transform": "id_reassign", "prefix": "dev_"}
        )
        
        assert change.metadata is not None
        assert change.metadata["transform"] == "id_reassign"


class TestObjectDiff:
    """Test ObjectDiff functionality"""
    
    def test_object_diff_creation(self):
        """Test creating object diff"""
        changes = [
            FieldChange("$.password", ChangeType.EXCLUDED, "secret", None),
            FieldChange("$.email", ChangeType.MASKED, "alice@example.com", "hash:abc123")
        ]
        
        diff = ObjectDiff(
            object_path="$.users[0]",
            object_meta={"path": "$.users[0]", "kind": "user"},
            changes=changes
        )
        
        assert diff.object_path == "$.users[0]"
        assert diff.change_count == 2
        assert len(diff.changes) == 2
    
    def test_object_diff_change_types(self):
        """Test getting change types from diff"""
        changes = [
            FieldChange("$.password", ChangeType.EXCLUDED, "secret", None),
            FieldChange("$.email", ChangeType.MASKED, "alice@example.com", "hash:abc123"),
            FieldChange("$.name", ChangeType.RENAMED, "Alice", "Alice")
        ]
        
        diff = ObjectDiff("$.users[0]", {}, changes)
        
        change_types = diff.change_types
        assert ChangeType.EXCLUDED in change_types
        assert ChangeType.MASKED in change_types
        assert ChangeType.RENAMED in change_types
        assert len(change_types) == 3
    
    def test_object_diff_has_change_type(self):
        """Test checking for specific change types"""
        changes = [
            FieldChange("$.password", ChangeType.EXCLUDED, "secret", None),
            FieldChange("$.email", ChangeType.MASKED, "alice@example.com", "hash:abc123")
        ]
        
        diff = ObjectDiff("$.users[0]", {}, changes)
        
        assert diff.has_change_type(ChangeType.EXCLUDED)
        assert diff.has_change_type(ChangeType.MASKED)
        assert not diff.has_change_type(ChangeType.RENAMED)
    
    def test_object_diff_get_changes_by_type(self):
        """Test getting changes by specific type"""
        changes = [
            FieldChange("$.password", ChangeType.EXCLUDED, "secret", None),
            FieldChange("$.token", ChangeType.EXCLUDED, "token123", None),
            FieldChange("$.email", ChangeType.MASKED, "alice@example.com", "hash:abc123")
        ]
        
        diff = ObjectDiff("$.users[0]", {}, changes)
        
        excluded_changes = diff.get_changes_by_type(ChangeType.EXCLUDED)
        assert len(excluded_changes) == 2
        assert all(c.change_type == ChangeType.EXCLUDED for c in excluded_changes)
        
        masked_changes = diff.get_changes_by_type(ChangeType.MASKED)
        assert len(masked_changes) == 1
        assert masked_changes[0].path == "$.email"


class TestCopyDiff:
    """Test CopyDiff functionality"""
    
    def test_diff_identical_objects(self):
        """Test diff of identical objects"""
        original = {"name": "Alice", "age": 30}
        copied = {"name": "Alice", "age": 30}
        meta = {"path": "$.user"}
        
        diff = CopyDiff.create(original, copied, meta)
        
        assert diff.object_path == "$.user"
        assert diff.change_count == 0
        assert len(diff.changes) == 0
    
    def test_diff_field_exclusion(self):
        """Test diff with field exclusion"""
        original = {"name": "Alice", "password": "secret", "email": "alice@example.com"}
        copied = {"name": "Alice", "email": "alice@example.com"}
        meta = {"path": "$.user"}
        
        diff = CopyDiff.create(original, copied, meta)
        
        assert diff.change_count == 1
        assert diff.changes[0].change_type == ChangeType.EXCLUDED
        assert diff.changes[0].path == "password"
        assert diff.changes[0].old_value == "secret"
        assert diff.changes[0].new_value is None
    
    def test_diff_field_masking(self):
        """Test diff with field masking"""
        original = {"name": "Alice", "email": "alice@example.com"}
        copied = {"name": "Alice", "email": "hash:abc123def456"}
        meta = {"path": "$.user"}
        
        diff = CopyDiff.create(original, copied, meta)
        
        assert diff.change_count == 1
        assert diff.changes[0].change_type == ChangeType.MASKED
        assert diff.changes[0].path == "email"
        assert diff.changes[0].old_value == "alice@example.com"
        assert diff.changes[0].new_value == "hash:abc123def456"
    
    def test_diff_field_addition(self):
        """Test diff with field addition"""
        original = {"name": "Alice"}
        copied = {"name": "Alice", "status": "active", "computed_field": "value"}
        meta = {"path": "$.user"}
        
        diff = CopyDiff.create(original, copied, meta)
        
        assert diff.change_count == 2
        
        # Check that additions are detected
        added_fields = [change.path for change in diff.changes]
        assert "status" in added_fields
        assert "computed_field" in added_fields
        
        # Check change types
        status_change = next(c for c in diff.changes if c.path == "status")
        assert status_change.change_type == ChangeType.DEFAULTED
        
        computed_change = next(c for c in diff.changes if c.path == "computed_field")
        assert computed_change.change_type == ChangeType.COMPUTED
    
    def test_diff_type_change(self):
        """Test diff with type change"""
        original = {"value": "123"}
        copied = {"value": 123}
        meta = {"path": "$.item"}
        
        diff = CopyDiff.create(original, copied, meta)
        
        assert diff.change_count == 1
        assert diff.changes[0].change_type == ChangeType.TYPE_CHANGED
        assert diff.changes[0].path == "value"
        assert diff.changes[0].old_value == "123"
        assert diff.changes[0].new_value == 123
    
    def test_diff_nested_objects(self):
        """Test diff with nested objects"""
        original = {
            "user": {
                "name": "Alice",
                "profile": {
                    "email": "alice@example.com",
                    "password": "secret"
                }
            }
        }
        copied = {
            "user": {
                "name": "Alice",
                "profile": {
                    "email": "hash:abc123"
                }
            }
        }
        meta = {"path": "$.data"}
        
        diff = CopyDiff.create(original, copied, meta)
        
        assert diff.change_count == 2
        
        # Check nested field changes
        paths = [change.path for change in diff.changes]
        assert "user.profile.password" in paths  # Excluded
        assert "user.profile.email" in paths     # Masked
        
        # Verify change types
        password_change = next(c for c in diff.changes if c.path == "user.profile.password")
        assert password_change.change_type == ChangeType.EXCLUDED
        
        email_change = next(c for c in diff.changes if c.path == "user.profile.email")
        assert email_change.change_type == ChangeType.MASKED
    
    def test_diff_non_dict_objects(self):
        """Test diff with non-dictionary objects"""
        original = "hello world"
        copied = "hello universe"
        meta = {"path": "$.message"}
        
        diff = CopyDiff.create(original, copied, meta)
        
        assert diff.change_count == 1
        assert diff.changes[0].change_type == ChangeType.MODIFIED
        assert diff.changes[0].path == "$"
        assert diff.changes[0].old_value == "hello world"
        assert diff.changes[0].new_value == "hello universe"
    
    def test_diff_masking_patterns(self):
        """Test detection of different masking patterns"""
        test_cases = [
            ("alice@example.com", "hash:abc123", ChangeType.MASKED),
            ("sensitive", "[REDACTED]", ChangeType.MASKED),
            ("password123", "********", ChangeType.MASKED),
            ("1234567890", "******7890", ChangeType.MASKED),
            ("normal", "changed", ChangeType.MODIFIED)
        ]
        
        for old_val, new_val, expected_type in test_cases:
            original = {"field": old_val}
            copied = {"field": new_val}
            meta = {"path": "$.test"}
            
            diff = CopyDiff.create(original, copied, meta)
            
            if expected_type == ChangeType.MODIFIED and new_val not in ["[REDACTED]"] and not new_val.startswith("hash:") and "*" not in new_val:
                assert diff.changes[0].change_type == expected_type
            else:
                assert diff.changes[0].change_type == ChangeType.MASKED


class TestCopyDiffSummarization:
    """Test diff summarization functionality"""
    
    def test_summarize_empty_diffs(self):
        """Test summarizing empty diff list"""
        summary = CopyDiff.summarize([])
        
        assert summary["summary"]["total_objects"] == 0
        assert summary["summary"]["total_changes"] == 0
        assert summary["summary"]["objects_with_changes"] == 0
        assert summary["summary"]["average_changes_per_object"] == 0
    
    def test_summarize_single_diff(self):
        """Test summarizing single diff"""
        changes = [
            FieldChange("$.password", ChangeType.EXCLUDED, "secret", None),
            FieldChange("$.email", ChangeType.MASKED, "alice@example.com", "hash:abc123")
        ]
        diff = ObjectDiff("$.users[0]", {}, changes)
        
        summary = CopyDiff.summarize([diff])
        
        assert summary["summary"]["total_objects"] == 1
        assert summary["summary"]["total_changes"] == 2
        assert summary["summary"]["objects_with_changes"] == 1
        assert summary["summary"]["average_changes_per_object"] == 2.0
        
        # Check change counts
        assert summary["change_counts"]["excluded"] == 1
        assert summary["change_counts"]["masked"] == 1
        
        # Check objects by change type
        assert summary["objects_by_change_type"]["excluded"] == 1
        assert summary["objects_by_change_type"]["masked"] == 1
    
    def test_summarize_multiple_diffs(self):
        """Test summarizing multiple diffs"""
        diff1 = ObjectDiff("$.users[0]", {}, [
            FieldChange("$.password", ChangeType.EXCLUDED, "secret", None)
        ])
        diff2 = ObjectDiff("$.users[1]", {}, [
            FieldChange("$.email", ChangeType.MASKED, "bob@example.com", "hash:def456"),
            FieldChange("$.name", ChangeType.RENAMED, "Bob", "Bob")
        ])
        diff3 = ObjectDiff("$.users[2]", {}, [])  # No changes
        
        summary = CopyDiff.summarize([diff1, diff2, diff3])
        
        assert summary["summary"]["total_objects"] == 3
        assert summary["summary"]["total_changes"] == 3
        assert summary["summary"]["objects_with_changes"] == 2
        assert summary["summary"]["average_changes_per_object"] == 1.0
        
        # Check most changed objects
        most_changed = summary["most_changed_objects"]
        assert len(most_changed) == 3
        assert most_changed[0]["path"] == "$.users[1]"  # 2 changes
        assert most_changed[0]["changes"] == 2
    
    def test_summarize_sample_changes(self):
        """Test sample changes in summary"""
        changes = [
            FieldChange("$.field1", ChangeType.EXCLUDED, "value1", None),
            FieldChange("$.field2", ChangeType.MASKED, "value2", "masked2"),
            FieldChange("$.field3", ChangeType.RENAMED, "value3", "value3")
        ]
        diff = ObjectDiff("$.object", {}, changes)
        
        summary = CopyDiff.summarize([diff])
        
        assert "sample_changes" in summary
        sample_changes = summary["sample_changes"]
        assert len(sample_changes) == 3
        
        # Check sample structure
        sample = sample_changes[0]
        assert "object_path" in sample
        assert "field_path" in sample
        assert "change_type" in sample
        assert "old_value" in sample
        assert "new_value" in sample


class TestDiffSerialization:
    """Test diff JSON serialization"""
    
    def test_diff_to_json(self):
        """Test converting diff to JSON"""
        changes = [
            FieldChange("$.password", ChangeType.EXCLUDED, "secret", None),
            FieldChange("$.email", ChangeType.MASKED, "alice@example.com", "hash:abc123")
        ]
        diff = ObjectDiff(
            object_path="$.users[0]",
            object_meta={"path": "$.users[0]", "kind": "user"},
            changes=changes
        )
        
        json_str = CopyDiff.to_json(diff)
        
        assert isinstance(json_str, str)
        assert "$.users[0]" in json_str
        assert "excluded" in json_str
        assert "masked" in json_str
    
    def test_diff_from_json(self):
        """Test creating diff from JSON"""
        changes = [
            FieldChange("$.password", ChangeType.EXCLUDED, "secret", None)
        ]
        original_diff = ObjectDiff(
            object_path="$.users[0]",
            object_meta={"path": "$.users[0]", "kind": "user"},
            changes=changes
        )
        
        json_str = CopyDiff.to_json(original_diff)
        restored_diff = CopyDiff.from_json(json_str)
        
        assert restored_diff.object_path == original_diff.object_path
        assert restored_diff.change_count == original_diff.change_count
        assert len(restored_diff.changes) == len(original_diff.changes)
        assert restored_diff.changes[0].change_type == ChangeType.EXCLUDED
    
    def test_diff_json_roundtrip(self):
        """Test JSON serialization roundtrip"""
        changes = [
            FieldChange(
                path="$.email",
                change_type=ChangeType.MASKED,
                old_value="alice@example.com",
                new_value="hash:abc123",
                metadata={"transform": "mask", "style": "hash"}
            )
        ]
        original_diff = ObjectDiff(
            object_path="$.users[0]",
            object_meta={"path": "$.users[0]", "kind": "user", "labels": ["pii"]},
            changes=changes
        )
        
        json_str = CopyDiff.to_json(original_diff)
        restored_diff = CopyDiff.from_json(json_str)
        
        # Check all properties are preserved
        assert restored_diff.object_path == original_diff.object_path
        assert restored_diff.object_meta == original_diff.object_meta
        assert restored_diff.change_count == original_diff.change_count
        
        original_change = original_diff.changes[0]
        restored_change = restored_diff.changes[0]
        assert restored_change.path == original_change.path
        assert restored_change.change_type == original_change.change_type
        assert restored_change.old_value == original_change.old_value
        assert restored_change.new_value == original_change.new_value
        assert restored_change.metadata == original_change.metadata


class TestDiffEdgeCases:
    """Test diff edge cases"""
    
    def test_diff_truncate_long_values(self):
        """Test truncation of very long values"""
        long_value = "x" * 200
        truncated = CopyDiff._truncate_value(long_value, max_length=50)
        
        assert len(truncated) == 53  # 50 + "..."
        assert truncated.endswith("...")
    
    def test_diff_truncate_short_values(self):
        """Test no truncation of short values"""
        short_value = "short"
        result = CopyDiff._truncate_value(short_value, max_length=50)
        
        assert result == short_value
    
    def test_diff_truncate_none_value(self):
        """Test truncation of None values"""
        result = CopyDiff._truncate_value(None)
        assert result is None
    
    def test_diff_infer_change_types(self):
        """Test change type inference"""
        # Test masking patterns
        assert CopyDiff._infer_change_type("alice@example.com", "hash:abc123") == ChangeType.MASKED
        assert CopyDiff._infer_change_type("password", "[REDACTED]") == ChangeType.MASKED
        assert CopyDiff._infer_change_type("secret", "***secret") == ChangeType.MASKED
        
        # Test type changes
        assert CopyDiff._infer_change_type("123", 123) == ChangeType.TYPE_CHANGED
        assert CopyDiff._infer_change_type([1, 2], (1, 2)) == ChangeType.TYPE_CHANGED
        
        # Test general modification
        assert CopyDiff._infer_change_type("old", "new") == ChangeType.MODIFIED
    
    def test_diff_infer_addition_types(self):
        """Test addition type inference"""
        # Test computed field detection
        assert CopyDiff._infer_addition_type("computed_name") == ChangeType.COMPUTED
        
        # Test default detection
        assert CopyDiff._infer_addition_type("default_value") == ChangeType.DEFAULTED
        assert CopyDiff._infer_addition_type(42) == ChangeType.DEFAULTED