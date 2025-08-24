"""
Unit tests for hierarchy merger module

Tests for HierarchyMerger class and merge strategies.
"""

import pytest
import copy
from unittest.mock import Mock, patch, MagicMock

from strataregula.hierarchy.merger import HierarchyMerger, MergeStrategy


class TestMergeStrategy:
    """Test MergeStrategy enum"""
    
    def test_merge_strategy_values(self):
        """Test merge strategy enumeration values"""
        assert MergeStrategy.DEEP_COPY.value == "deep_copy"
        assert MergeStrategy.MERGE.value == "merge"
        assert MergeStrategy.APPEND.value == "append"
        assert MergeStrategy.SMART.value == "smart"


class TestHierarchyMerger:
    """Test HierarchyMerger functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.merger = HierarchyMerger()
    
    def test_init_default_strategy(self):
        """Test default initialization"""
        merger = HierarchyMerger()
        assert merger.strategy == MergeStrategy.SMART
    
    def test_init_custom_strategy(self):
        """Test initialization with custom strategy"""
        merger = HierarchyMerger(MergeStrategy.DEEP_COPY)
        assert merger.strategy == MergeStrategy.DEEP_COPY
    
    def test_merge_basic_types(self):
        """Test merging basic types"""
        base = "original"
        override = "new"
        
        result = self.merger.merge(base, override)
        
        assert result == "new"
        assert result is not override  # Should be deep copied
    
    def test_merge_integers(self):
        """Test merging integers"""
        base = 42
        override = 100
        
        result = self.merger.merge(base, override)
        assert result == 100
    
    def test_merge_none_values(self):
        """Test merging None values"""
        base = None
        override = "value"
        
        result = self.merger.merge(base, override)
        assert result == "value"
        
        # Test reverse
        base = "value"
        override = None
        result = self.merger.merge(base, override)
        assert result is None


class TestDictMerging:
    """Test dictionary merging functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.merger = HierarchyMerger()
    
    def test_merge_simple_dicts(self):
        """Test merging simple dictionaries"""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        
        result = self.merger.merge(base, override)
        
        assert result == {"a": 1, "b": 3, "c": 4}
        assert result is not base
        assert result is not override
    
    def test_merge_nested_dicts(self):
        """Test merging nested dictionaries"""
        base = {
            "level1": {
                "level2": {
                    "existing": "value",
                    "to_override": "old"
                }
            }
        }
        override = {
            "level1": {
                "level2": {
                    "to_override": "new",
                    "new_key": "added"
                }
            }
        }
        
        result = self.merger.merge(base, override)
        
        expected = {
            "level1": {
                "level2": {
                    "existing": "value",
                    "to_override": "new",
                    "new_key": "added"
                }
            }
        }
        assert result == expected
    
    def test_merge_dict_with_different_types(self):
        """Test merging dictionary with different value types"""
        base = {"key": {"nested": "value"}}
        override = {"key": "string_replacement"}
        
        result = self.merger.merge(base, override)
        
        assert result == {"key": "string_replacement"}
    
    def test_merge_empty_dicts(self):
        """Test merging empty dictionaries"""
        base = {}
        override = {"new": "value"}
        
        result = self.merger.merge(base, override)
        assert result == {"new": "value"}
        
        # Test reverse
        base = {"existing": "value"}
        override = {}
        result = self.merger.merge(base, override)
        assert result == {"existing": "value"}


class TestListMerging:
    """Test list merging functionality"""
    
    def test_list_merge_deep_copy_strategy(self):
        """Test list merging with DEEP_COPY strategy"""
        merger = HierarchyMerger(MergeStrategy.DEEP_COPY)
        base = [1, 2, 3]
        override = [4, 5]
        
        result = merger.merge(base, override)
        
        assert result == [4, 5]
        assert result is not override
    
    def test_list_merge_append_strategy(self):
        """Test list merging with APPEND strategy"""
        merger = HierarchyMerger(MergeStrategy.APPEND)
        base = [1, 2, 3]
        override = [4, 5]
        
        result = merger.merge(base, override)
        
        assert result == [1, 2, 3, 4, 5]
    
    def test_list_merge_merge_strategy(self):
        """Test list merging with MERGE strategy"""
        merger = HierarchyMerger(MergeStrategy.MERGE)
        base = [{"a": 1}, {"b": 2}, {"c": 3}]
        override = [{"a": 10}, {"b": 20}]
        
        result = merger.merge(base, override)
        
        expected = [{"a": 10}, {"b": 20}, {"c": 3}]
        assert result == expected
    
    def test_list_merge_smart_strategy_simple_types(self):
        """Test list merging with SMART strategy for simple types"""
        merger = HierarchyMerger(MergeStrategy.SMART)
        base = [1, 2, 3]
        override = [4, 5]
        
        result = merger.merge(base, override)
        
        # Smart strategy should replace simple types
        assert result == [4, 5]
    
    def test_list_merge_smart_strategy_config_objects(self):
        """Test list merging with SMART strategy for config objects"""
        merger = HierarchyMerger(MergeStrategy.SMART)
        base = [{"config": "base"}, {"other": "value"}]
        override = [{"config": "override"}]
        
        result = merger.merge(base, override)
        
        # Smart strategy should merge config objects by index
        expected = [{"config": "override"}, {"other": "value"}]
        assert result == expected
    
    def test_list_merge_smart_strategy_mixed_types(self):
        """Test list merging with SMART strategy for mixed types"""
        merger = HierarchyMerger(MergeStrategy.SMART)
        base = [1, {"config": "base"}]
        override = [2, "string"]
        
        result = merger.merge(base, override)
        
        # Smart strategy should append mixed types
        assert result == [1, {"config": "base"}, 2, "string"]
    
    def test_are_simple_types(self):
        """Test _are_simple_types helper method"""
        merger = HierarchyMerger()
        
        # Simple types
        assert merger._are_simple_types([1, 2, 3])
        assert merger._are_simple_types(["a", "b", "c"])
        assert merger._are_simple_types([1, "mixed", 3.14, True, None])
        
        # Not simple types
        assert not merger._are_simple_types([1, {"dict": "here"}])
        assert not merger._are_simple_types([{"all": "dicts"}])
        assert not merger._are_simple_types([[1, 2, 3]])
    
    def test_are_config_objects(self):
        """Test _are_config_objects helper method"""
        merger = HierarchyMerger()
        
        # Config objects (all dicts)
        assert merger._are_config_objects([{"a": 1}, {"b": 2}])
        assert merger._are_config_objects([{}])
        
        # Not config objects
        assert not merger._are_config_objects([1, 2, 3])
        assert not merger._are_config_objects([{"a": 1}, "string"])
        assert not merger._are_config_objects([[1, 2], [3, 4]])


class TestMultipleMerging:
    """Test merging multiple configurations"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.merger = HierarchyMerger()
    
    def test_merge_multiple_empty_list(self):
        """Test merging empty list"""
        result = self.merger.merge_multiple([])
        assert result == {}
    
    def test_merge_multiple_single_config(self):
        """Test merging single configuration"""
        configs = [{"a": 1, "b": 2}]
        result = self.merger.merge_multiple(configs)
        
        assert result == {"a": 1, "b": 2}
        assert result is not configs[0]  # Should be deep copied
    
    def test_merge_multiple_configs(self):
        """Test merging multiple configurations"""
        configs = [
            {"a": 1, "common": "base"},
            {"b": 2, "common": "override1"},
            {"c": 3, "common": "override2"}
        ]
        
        result = self.merger.merge_multiple(configs)
        
        expected = {"a": 1, "b": 2, "c": 3, "common": "override2"}
        assert result == expected
    
    def test_merge_multiple_nested_configs(self):
        """Test merging multiple nested configurations"""
        configs = [
            {"database": {"host": "localhost", "port": 5432}},
            {"database": {"username": "user", "password": "pass"}},
            {"database": {"ssl": True}}
        ]
        
        result = self.merger.merge_multiple(configs)
        
        expected = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "user",
                "password": "pass",
                "ssl": True
            }
        }
        assert result == expected


class TestEnvironmentMerging:
    """Test environment-specific merging"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.merger = HierarchyMerger()
    
    def test_merge_with_environment_match(self):
        """Test merging with matching environment"""
        base = {"app": "base_config"}
        env_config = {"app": "env_config", "environment": "production"}
        
        result = self.merger.merge_with_environment(base, env_config, "production")
        
        expected = {"app": "env_config", "environment": "production"}
        assert result == expected
    
    def test_merge_with_environment_no_match(self):
        """Test merging with non-matching environment"""
        base = {"app": "base_config"}
        env_config = {"app": "env_config", "environment": "production"}
        
        result = self.merger.merge_with_environment(base, env_config, "development")
        
        # Should return deep copy of base when no match
        assert result == {"app": "base_config"}
        assert result is not base
    
    def test_merge_with_environment_missing_env_key(self):
        """Test merging with config missing environment key"""
        base = {"app": "base_config"}
        env_config = {"app": "env_config"}  # No environment key
        
        result = self.merger.merge_with_environment(base, env_config, "production")
        
        # Should return base config when environment key is missing
        assert result == {"app": "base_config"}


class TestConflictResolution:
    """Test conflict resolution functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.merger = HierarchyMerger()
    
    def test_resolve_conflicts_empty(self):
        """Test resolving empty conflicts"""
        base = {"app": "base"}
        result = self.merger.resolve_conflicts(base, [])
        
        assert result == {"app": "base"}
        assert result is not base
    
    def test_resolve_conflicts_without_priority(self):
        """Test resolving conflicts without priority order"""
        base = {"app": "base"}
        conflicts = [
            {"app": "conflict1", "feature": "a"},
            {"app": "conflict2", "feature": "b"}
        ]
        
        result = self.merger.resolve_conflicts(base, conflicts)
        
        # Should merge in order given
        expected = {"app": "conflict2", "feature": "b"}
        assert result == expected
    
    def test_resolve_conflicts_with_priority(self):
        """Test resolving conflicts with priority order"""
        base = {"app": "base"}
        conflicts = [
            {"app": "high", "priority": "high"},
            {"app": "low", "priority": "low"},
            {"app": "medium", "priority": "medium"}
        ]
        priority_order = ["low", "medium", "high"]
        
        result = self.merger.resolve_conflicts(base, conflicts, priority_order)
        
        # Should merge in priority order (low -> medium -> high)
        expected = {"app": "high", "priority": "high"}
        assert result == expected
    
    def test_resolve_conflicts_unknown_priority(self):
        """Test resolving conflicts with unknown priority"""
        base = {"app": "base"}
        conflicts = [
            {"app": "known", "priority": "high"},
            {"app": "unknown", "priority": "unknown_priority"}
        ]
        priority_order = ["high"]
        
        result = self.merger.resolve_conflicts(base, conflicts, priority_order)
        
        # Unknown priority should be processed last
        expected = {"app": "unknown", "priority": "unknown_priority"}
        assert result == expected
    
    def test_sort_by_priority(self):
        """Test _sort_by_priority helper method"""
        conflicts = [
            {"name": "third", "priority": "low"},
            {"name": "first", "priority": "high"},
            {"name": "second", "priority": "medium"},
            {"name": "last", "priority": "unknown"}
        ]
        priority_order = ["high", "medium", "low"]
        
        sorted_conflicts = self.merger._sort_by_priority(conflicts, priority_order)
        
        names = [c["name"] for c in sorted_conflicts]
        assert names == ["first", "second", "third", "last"]


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.merger = HierarchyMerger()
    
    def test_merge_none_values(self):
        """Test merging with None values"""
        assert self.merger.merge(None, {"key": "value"}) == {"key": "value"}
        assert self.merger.merge({"key": "value"}, None) is None
        assert self.merger.merge(None, None) is None
    
    def test_merge_mixed_types(self):
        """Test merging incompatible types"""
        base = {"key": [1, 2, 3]}
        override = {"key": {"nested": "dict"}}
        
        result = self.merger.merge(base, override)
        
        # Override should win for mixed types
        assert result == {"key": {"nested": "dict"}}
    
    def test_merge_circular_references(self):
        """Test handling of circular references"""
        base = {"a": 1}
        base["self"] = base  # Create circular reference
        
        override = {"b": 2}
        
        # Should handle circular references gracefully
        result = self.merger.merge(base, override)
        
        assert "a" in result
        assert "b" in result
        assert "self" in result


class TestPerformance:
    """Test performance characteristics"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.merger = HierarchyMerger()
    
    def test_large_dict_merge(self):
        """Test merging large dictionaries"""
        # Create large dictionaries
        base = {f"key_{i}": f"value_{i}" for i in range(1000)}
        override = {f"key_{i}": f"override_{i}" for i in range(500, 1500)}
        
        result = self.merger.merge(base, override)
        
        # Verify merge worked correctly
        assert len(result) == 1500
        assert result["key_0"] == "value_0"  # From base
        assert result["key_750"] == "override_750"  # From override
        assert result["key_1400"] == "override_1400"  # New from override
    
    def test_deep_nesting_merge(self):
        """Test merging deeply nested structures"""
        # Create deeply nested structure
        def create_nested_dict(depth, value):
            if depth == 0:
                return value
            return {"level": create_nested_dict(depth - 1, value)}
        
        base = create_nested_dict(10, "base")
        override = create_nested_dict(10, "override")
        
        result = self.merger.merge(base, override)
        
        # Navigate to deepest level to verify merge
        current = result
        for _ in range(10):
            current = current["level"]
        assert current == "override"


class TestLogging:
    """Test logging functionality"""
    
    @patch('strataregula.hierarchy.merger.logger')
    def test_logging_on_init(self, mock_logger):
        """Test logging on initialization"""
        HierarchyMerger(MergeStrategy.DEEP_COPY)
        
        mock_logger.debug.assert_called_with(
            "Initialized HierarchyMerger with strategy: deep_copy"
        )
    
    @patch('strataregula.hierarchy.merger.logger')
    def test_logging_during_merge(self, mock_logger):
        """Test logging during merge operations"""
        merger = HierarchyMerger()
        base = {"nested": {"key": "value"}}
        override = {"nested": {"key": "new_value"}}
        
        merger.merge(base, override)
        
        # Verify debug logging calls were made
        assert mock_logger.debug.called
        debug_calls = [call.args[0] for call in mock_logger.debug.call_args_list]
        
        assert any("Merging with strategy" in call for call in debug_calls)
        assert any("Recursive merge for key" in call for call in debug_calls)