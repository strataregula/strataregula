"""
Tests for protocols sse module
"""

import pytest
import time
import json
import uuid
from unittest.mock import Mock, patch

from strataregula.protocols.sse import (
    SSEConfig, SSEEvent, SSEConnection, AIOHTTP_AVAILABLE
)


class TestSSEConfig:
    """Test SSEConfig dataclass"""

    def test_sse_config_defaults(self):
        """Test SSEConfig creation with default values"""
        config = SSEConfig()
        
        assert config.host == "localhost"
        assert config.port == 8080
        assert config.path == "/events"
        assert config.keepalive_interval == 30.0
        assert config.retry_time == 3000
        assert config.cors_origins == {"*"}
        assert config.max_connections == 1000
        assert config.buffer_size == 1024
        assert config.compression is True

    def test_sse_config_custom_values(self):
        """Test SSEConfig creation with custom values"""
        custom_origins = {"http://example.com", "https://test.com"}
        
        config = SSEConfig(
            host="example.com",
            port=9090,
            path="/custom-events",
            keepalive_interval=60.0,
            retry_time=5000,
            cors_origins=custom_origins,
            max_connections=500,
            buffer_size=2048,
            compression=False
        )
        
        assert config.host == "example.com"
        assert config.port == 9090
        assert config.path == "/custom-events"
        assert config.keepalive_interval == 60.0
        assert config.retry_time == 5000
        assert config.cors_origins == custom_origins
        assert config.max_connections == 500
        assert config.buffer_size == 2048
        assert config.compression is False

    def test_sse_config_cors_origins_default_factory(self):
        """Test that cors_origins set is created as new instance for each config"""
        config1 = SSEConfig()
        config2 = SSEConfig()
        
        # Modify one config's origins
        config1.cors_origins.add("http://test.com")
        
        # Other config should not be affected
        assert "http://test.com" not in config2.cors_origins
        assert config2.cors_origins == {"*"}


class TestSSEEvent:
    """Test SSEEvent dataclass"""

    def test_sse_event_minimal_creation(self):
        """Test SSEEvent creation with minimal fields"""
        event = SSEEvent(data="test message")
        
        assert event.data == "test message"
        assert event.event_type is None
        assert isinstance(event.event_id, str)
        assert event.retry is None
        assert isinstance(event.timestamp, float)

    def test_sse_event_full_creation(self):
        """Test SSEEvent creation with all fields"""
        timestamp = time.time()
        event_id = str(uuid.uuid4())
        
        event = SSEEvent(
            data={"message": "test"},
            event_type="custom",
            event_id=event_id,
            retry=5000,
            timestamp=timestamp
        )
        
        assert event.data == {"message": "test"}
        assert event.event_type == "custom"
        assert event.event_id == event_id
        assert event.retry == 5000
        assert event.timestamp == timestamp

    def test_sse_event_id_auto_generation(self):
        """Test that SSEEvent automatically generates unique event IDs"""
        event1 = SSEEvent(data="test1")
        event2 = SSEEvent(data="test2")
        
        assert event1.event_id != event2.event_id
        assert isinstance(event1.event_id, str)
        assert isinstance(event2.event_id, str)
        assert len(event1.event_id) > 0
        assert len(event2.event_id) > 0

    def test_sse_event_timestamp_auto_generation(self):
        """Test that SSEEvent automatically generates timestamp"""
        before = time.time()
        event = SSEEvent(data="test")
        after = time.time()
        
        assert before <= event.timestamp <= after

    def test_sse_event_format_minimal(self):
        """Test formatting SSEEvent with minimal fields"""
        event = SSEEvent(data="Hello World")
        # Set a known event_id for testing
        event.event_id = "test-id-123"
        
        formatted = event.format()
        
        assert "id: test-id-123" in formatted
        assert "data: Hello World" in formatted
        assert formatted.endswith("\n\n")
        # Should not contain event type or retry
        assert "event:" not in formatted
        assert "retry:" not in formatted

    def test_sse_event_format_with_event_type(self):
        """Test formatting SSEEvent with event type"""
        event = SSEEvent(
            data="Test message",
            event_type="notification",
            event_id="test-123"
        )
        
        formatted = event.format()
        
        assert "event: notification" in formatted
        assert "id: test-123" in formatted
        assert "data: Test message" in formatted

    def test_sse_event_format_with_retry(self):
        """Test formatting SSEEvent with retry value"""
        event = SSEEvent(
            data="Test message",
            retry=5000,
            event_id="test-123"
        )
        
        formatted = event.format()
        
        assert "retry: 5000" in formatted
        assert "id: test-123" in formatted
        assert "data: Test message" in formatted

    def test_sse_event_format_dict_data(self):
        """Test formatting SSEEvent with dictionary data"""
        data = {"message": "Hello", "type": "greeting", "count": 1}
        event = SSEEvent(data=data, event_id="test-123")
        
        formatted = event.format()
        
        assert "id: test-123" in formatted
        assert "data:" in formatted
        
        # Should contain JSON representation of the data
        expected_json = json.dumps(data)
        assert f"data: {expected_json}" in formatted

    def test_sse_event_format_multiline_data(self):
        """Test formatting SSEEvent with multiline string data"""
        multiline_data = "Line 1\nLine 2\nLine 3"
        event = SSEEvent(data=multiline_data, event_id="test-123")
        
        formatted = event.format()
        
        # Each line should be prefixed with "data: "
        assert "data: Line 1" in formatted
        assert "data: Line 2" in formatted
        assert "data: Line 3" in formatted
        assert "id: test-123" in formatted

    def test_sse_event_format_complete(self):
        """Test formatting SSEEvent with all fields"""
        data = {"message": "Complete test"}
        event = SSEEvent(
            data=data,
            event_type="test-event",
            event_id="complete-123",
            retry=3000
        )
        
        formatted = event.format()
        
        expected_lines = [
            "event: test-event",
            "id: complete-123",
            "retry: 3000",
            f"data: {json.dumps(data)}",
            "",
            ""
        ]
        
        assert formatted == "\n".join(expected_lines)

    def test_sse_event_format_without_event_id(self):
        """Test formatting SSEEvent when event_id is None"""
        event = SSEEvent(data="test", event_id=None)
        
        formatted = event.format()
        
        assert "data: test" in formatted
        assert "id:" not in formatted
        assert formatted.endswith("\n\n")

    def test_sse_event_format_empty_data(self):
        """Test formatting SSEEvent with empty data"""
        event = SSEEvent(data="", event_id="empty-test")
        
        formatted = event.format()
        
        assert "id: empty-test" in formatted
        assert "data:" in formatted
        assert formatted.endswith("\n\n")

    def test_sse_event_data_types(self):
        """Test SSEEvent with different data types"""
        # String data
        event1 = SSEEvent(data="string data")
        assert event1.data == "string data"
        
        # Dictionary data
        dict_data = {"key": "value", "number": 42}
        event2 = SSEEvent(data=dict_data)
        assert event2.data == dict_data
        
        # List data (should work as it's JSON serializable)
        list_data = [1, 2, 3, "test"]
        event3 = SSEEvent(data=list_data)
        assert event3.data == list_data
        
        # Number data
        event4 = SSEEvent(data=42)
        assert event4.data == 42


class TestSSEConnection:
    """Test SSEConnection class (basic structure test)"""

    def test_sse_connection_exists(self):
        """Test that SSEConnection class exists and can be imported"""
        # This is a basic test to ensure the class is properly defined
        # More detailed tests would require actual connection objects
        assert SSEConnection is not None
        assert hasattr(SSEConnection, '__init__') or callable(SSEConnection)

    @patch('strataregula.protocols.sse.AIOHTTP_AVAILABLE', False)
    def test_sse_without_aiohttp_library(self):
        """Test SSE module behavior when aiohttp is not available"""
        # Should still be able to create events and configs
        config = SSEConfig()
        assert isinstance(config, SSEConfig)
        
        event = SSEEvent(data="test")
        assert event.data == "test"
        formatted = event.format()
        assert "data: test" in formatted

    def test_sse_config_path_validation(self):
        """Test SSEConfig path settings"""
        # Test default path
        config = SSEConfig()
        assert config.path == "/events"
        
        # Test custom paths
        config_custom = SSEConfig(path="/api/stream")
        assert config_custom.path == "/api/stream"
        
        config_root = SSEConfig(path="/")
        assert config_root.path == "/"

    def test_sse_config_performance_settings(self):
        """Test SSEConfig performance-related settings"""
        config = SSEConfig(
            max_connections=2000,
            buffer_size=4096,
            keepalive_interval=45.0
        )
        
        assert config.max_connections == 2000
        assert config.buffer_size == 4096
        assert config.keepalive_interval == 45.0