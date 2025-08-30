"""Tests for index base functionality."""

import pytest
from strataregula.index.base import IndexProvider


class TestIndexProvider:
    """Test IndexProvider interface."""
    
    def test_index_provider_interface(self):
        """Test that IndexProvider defines the expected interface."""
        # This is a protocol, so we just check it exists
        assert hasattr(IndexProvider, '__annotations__')
        assert 'name' in IndexProvider.__annotations__
        assert 'version' in IndexProvider.__annotations__