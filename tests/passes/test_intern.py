"""
Tests for the InternPass configuration interning functionality.
"""

import pytest

from strataregula.passes import InternPass


class TestInternPass:
    """Test suite for InternPass functionality."""

    def test_intern_pass_basic(self):
        """Test basic interning functionality."""
        pass_instance = InternPass()

        # Test configuration with duplicate values
        config = {
            "service_a": {"timeout": 30, "retries": 3},
            "service_b": {"timeout": 30, "retries": 3},  # Duplicate values
            "service_c": {"timeout": 60, "retries": 2},
        }

        result = pass_instance.run(config)

        # Should return a configuration (exact structure may be interned)
        assert result is not None
        assert isinstance(result, dict) or hasattr(result, "items")

    def test_intern_pass_with_stats(self):
        """Test InternPass with statistics collection."""
        pass_instance = InternPass(collect_stats=True)

        config = {
            "duplicate_value": "test",
            "another_duplicate": "test",  # Same string
            "different": "other",
        }

        pass_instance.run(config)
        stats = pass_instance.get_stats()

        # Should collect some statistics
        assert isinstance(stats, dict)
        assert "nodes_processed" in stats
        assert "unique_values" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "hit_rate" in stats

    def test_intern_pass_float_quantization(self):
        """Test InternPass with float quantization."""
        pass_instance = InternPass(qfloat=0.1)

        config = {
            "value1": 1.23456,  # Should be quantized
            "value2": 1.28901,  # Should be quantized to similar value
            "value3": 2.0,
        }

        result = pass_instance.run(config)

        # Should process without errors
        assert result is not None

    def test_intern_pass_empty_config(self):
        """Test InternPass with empty configuration."""
        pass_instance = InternPass()

        config = {}
        result = pass_instance.run(config)

        # Should handle empty config
        assert result is not None

    def test_intern_pass_nested_structures(self):
        """Test InternPass with nested data structures."""
        pass_instance = InternPass(collect_stats=True)

        config = {
            "nested": {
                "level1": {
                    "level2": ["item1", "item2", "item1"]  # Duplicate items
                }
            },
            "list_data": [1, 2, 3, 1, 2],  # Duplicate numbers
            "sets": {"a", "b"},  # Set with duplicates
        }

        result = pass_instance.run(config)
        stats = pass_instance.get_stats()

        # Should process nested structures
        assert result is not None
        assert stats["nodes_processed"] > 0


if __name__ == "__main__":
    pytest.main([__file__])
