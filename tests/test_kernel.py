"""
Tests for the StrataRegula Kernel functionality.
"""

from collections.abc import Mapping
from typing import Any

import pytest

from strataregula import InternPass, Kernel


class MockView:
    """Mock view for testing."""

    def __init__(self, key: str):
        self.key = key

    def materialize(self, model: Mapping[str, Any], **params) -> Any:
        """Simple materialization that returns a subset of the model."""
        return {"view": self.key, "data": dict(model), "params": params}


class MockPass:
    """Mock pass for testing."""

    def run(self, model: Mapping[str, Any]) -> Mapping[str, Any]:
        """Simple pass that adds a marker."""
        result = dict(model)
        result["_processed_by_mock_pass"] = True
        return result


class TestKernel:
    """Test suite for Kernel functionality."""

    def test_kernel_creation(self):
        """Test basic kernel creation."""
        kernel = Kernel()

        assert kernel is not None
        assert len(kernel.passes) == 0
        assert len(kernel.views) == 0
        assert kernel.stats.total_queries == 0

    def test_kernel_register_pass(self):
        """Test registering compile passes."""
        kernel = Kernel()
        mock_pass = MockPass()

        kernel.register_pass(mock_pass)

        assert len(kernel.passes) == 1
        assert kernel.passes[0] is mock_pass

    def test_kernel_register_view(self):
        """Test registering views."""
        kernel = Kernel()
        mock_view = MockView("test_view")

        kernel.register_view(mock_view)

        assert len(kernel.views) == 1
        assert "test_view" in kernel.views
        assert kernel.views["test_view"] is mock_view

    def test_kernel_query_basic(self):
        """Test basic query functionality."""
        kernel = Kernel()
        mock_view = MockView("test_view")
        kernel.register_view(mock_view)

        config = {"service": "test", "timeout": 30}
        params = {"format": "json"}

        result = kernel.query("test_view", params, config)

        assert result is not None
        assert result["view"] == "test_view"
        assert result["data"]["service"] == "test"
        assert result["params"]["format"] == "json"
        assert kernel.stats.total_queries == 1

    def test_kernel_query_with_pass(self):
        """Test query with compile passes."""
        kernel = Kernel()
        mock_pass = MockPass()
        mock_view = MockView("test_view")

        kernel.register_pass(mock_pass)
        kernel.register_view(mock_view)

        config = {"original": "data"}
        result = kernel.query("test_view", {}, config)

        # Should have been processed by the pass
        assert result["data"]["_processed_by_mock_pass"] is True
        assert result["data"]["original"] == "data"

    def test_kernel_query_caching(self):
        """Test that queries are cached properly."""
        kernel = Kernel()
        mock_view = MockView("test_view")
        kernel.register_view(mock_view)

        config = {"service": "test"}
        params = {"format": "json"}

        # First query - should be a cache miss
        result1 = kernel.query("test_view", params, config)
        assert kernel.stats.misses == 1
        assert kernel.stats.hits == 0

        # Second identical query - should be a cache hit
        result2 = kernel.query("test_view", params, config)
        assert kernel.stats.misses == 1
        assert kernel.stats.hits == 1

        # Results should be identical
        assert result1 == result2

    def test_kernel_query_nonexistent_view(self):
        """Test querying a view that doesn't exist."""
        kernel = Kernel()

        config = {"service": "test"}

        with pytest.raises(KeyError) as exc_info:
            kernel.query("nonexistent_view", {}, config)

        assert "nonexistent_view" in str(exc_info.value)

    def test_kernel_with_intern_pass(self):
        """Test kernel with actual InternPass."""
        kernel = Kernel()
        intern_pass = InternPass(collect_stats=True)
        mock_view = MockView("intern_view")

        kernel.register_pass(intern_pass)
        kernel.register_view(mock_view)

        config = {
            "service_a": {"timeout": 30},
            "service_b": {"timeout": 30},  # Duplicate value
        }

        result = kernel.query("intern_view", {}, config)

        # Should have processed successfully
        assert result is not None
        assert result["view"] == "intern_view"
        # Data may have been interned, but should still contain the services
        data = result["data"]
        assert "service_a" in data or hasattr(data, "items")

    def test_kernel_stats(self):
        """Test kernel statistics collection."""
        kernel = Kernel()
        mock_view = MockView("stats_view")
        kernel.register_view(mock_view)

        config = {"test": "data"}

        # Make a few queries
        kernel.query("stats_view", {"param1": "value1"}, config)
        kernel.query("stats_view", {"param2": "value2"}, config)  # Different params
        kernel.query("stats_view", {"param1": "value1"}, config)  # Same as first

        stats = kernel.get_stats()

        assert stats["total_queries"] == 3
        assert stats["cache_hits"] == 1  # Third query should be cached
        assert stats["cache_misses"] == 2  # First two should be misses
        assert "registered_passes" in stats
        assert "registered_views" in stats
        assert "stats_view" in stats["registered_views"]

    def test_kernel_clear_cache(self):
        """Test cache clearing functionality."""
        kernel = Kernel()
        mock_view = MockView("cache_view")
        kernel.register_view(mock_view)

        config = {"test": "data"}

        # Query to populate cache
        kernel.query("cache_view", {}, config)
        assert kernel.stats.misses == 1

        # Query again - should be cached
        kernel.query("cache_view", {}, config)
        assert kernel.stats.hits == 1

        # Clear cache
        kernel.clear_cache()

        # Query again - should be a miss since cache was cleared
        kernel.query("cache_view", {}, config)
        assert kernel.stats.misses == 2

    def test_kernel_stats_visualization(self):
        """Test statistics visualization."""
        kernel = Kernel()
        mock_view = MockView("viz_view")
        kernel.register_view(mock_view)

        config = {"test": "data"}
        kernel.query("viz_view", {}, config)

        visualization = kernel.get_stats_visualization()

        assert isinstance(visualization, str)
        assert "StrataRegula Kernel Stats" in visualization
        assert "Cache Performance" in visualization
        assert "Queries:" in visualization


if __name__ == "__main__":
    pytest.main([__file__])
