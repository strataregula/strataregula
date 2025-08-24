"""
Tests for protocols websocket module
"""

import pytest
import time
import json
import ssl
from unittest.mock import Mock, patch, MagicMock

from strataregula.protocols.websocket import (
    WebSocketConfig, WebSocketMessage, WebSocketHandler, WEBSOCKETS_AVAILABLE
)


class TestWebSocketConfig:
    """Test WebSocketConfig dataclass"""

    def test_websocket_config_defaults(self):
        """Test WebSocketConfig creation with default values"""
        config = WebSocketConfig()
        
        assert config.host == "localhost"
        assert config.port == 8765
        assert config.path == "/"
        assert config.ping_interval == 20.0
        assert config.ping_timeout == 20.0
        assert config.close_timeout == 10.0
        assert config.max_size == 2**20  # 1MB
        assert config.max_queue == 32
        assert config.compression is None
        assert config.ssl_context is None
        assert config.extra_headers == {}

    def test_websocket_config_custom_values(self):
        """Test WebSocketConfig creation with custom values"""
        ssl_context = ssl.create_default_context()
        extra_headers = {"Authorization": "Bearer token"}
        
        config = WebSocketConfig(
            host="example.com",
            port=9001,
            path="/ws",
            ping_interval=30.0,
            ping_timeout=15.0,
            close_timeout=5.0,
            max_size=2**21,  # 2MB
            max_queue=64,
            compression="deflate",
            ssl_context=ssl_context,
            extra_headers=extra_headers
        )
        
        assert config.host == "example.com"
        assert config.port == 9001
        assert config.path == "/ws"
        assert config.ping_interval == 30.0
        assert config.ping_timeout == 15.0
        assert config.close_timeout == 5.0
        assert config.max_size == 2**21
        assert config.max_queue == 64
        assert config.compression == "deflate"
        assert config.ssl_context is ssl_context
        assert config.extra_headers == extra_headers

    def test_websocket_config_extra_headers_default_factory(self):
        """Test that extra_headers dict is created as new instance for each config"""
        config1 = WebSocketConfig()
        config2 = WebSocketConfig()
        
        # Modify one config's headers
        config1.extra_headers["Custom-Header"] = "value"
        
        # Other config should not be affected
        assert "Custom-Header" not in config2.extra_headers

    def test_websocket_config_optional_fields(self):
        """Test WebSocketConfig with None values for optional fields"""
        config = WebSocketConfig(
            ping_interval=None,
            ping_timeout=None,
            close_timeout=None,
            max_size=None,
            max_queue=None
        )
        
        assert config.ping_interval is None
        assert config.ping_timeout is None
        assert config.close_timeout is None
        assert config.max_size is None
        assert config.max_queue is None


class TestWebSocketMessage:
    """Test WebSocketMessage dataclass"""

    def test_websocket_message_minimal_creation(self):
        """Test WebSocketMessage creation with minimal fields"""
        message = WebSocketMessage(data="Hello World")
        
        assert message.data == "Hello World"
        assert message.message_type == "text"
        assert isinstance(message.timestamp, float)
        assert message.client_id is None

    def test_websocket_message_full_creation(self):
        """Test WebSocketMessage creation with all fields"""
        timestamp = time.time()
        binary_data = b"binary data"
        
        message = WebSocketMessage(
            data=binary_data,
            message_type="binary",
            timestamp=timestamp,
            client_id="client123"
        )
        
        assert message.data == binary_data
        assert message.message_type == "binary"
        assert message.timestamp == timestamp
        assert message.client_id == "client123"

    def test_websocket_message_timestamp_auto_generation(self):
        """Test that WebSocketMessage automatically generates timestamp"""
        before = time.time()
        message = WebSocketMessage(data="test")
        after = time.time()
        
        assert before <= message.timestamp <= after

    def test_websocket_message_text_type(self):
        """Test WebSocketMessage with text message type"""
        message = WebSocketMessage(
            data="Text message",
            message_type="text"
        )
        
        assert message.data == "Text message"
        assert message.message_type == "text"

    def test_websocket_message_binary_type(self):
        """Test WebSocketMessage with binary message type"""
        binary_data = b'\x00\x01\x02\x03'
        message = WebSocketMessage(
            data=binary_data,
            message_type="binary"
        )
        
        assert message.data == binary_data
        assert message.message_type == "binary"

    def test_websocket_message_json_type(self):
        """Test WebSocketMessage with JSON message type"""
        json_data = {"key": "value", "number": 42}
        message = WebSocketMessage(
            data=json_data,
            message_type="json"
        )
        
        assert message.data == json_data
        assert message.message_type == "json"

    def test_websocket_message_to_json_text_type(self):
        """Test WebSocketMessage to_json conversion for text type"""
        timestamp = 1234567890.0
        message = WebSocketMessage(
            data="Hello World",
            message_type="text",
            timestamp=timestamp,
            client_id="test_client"
        )
        
        result = message.to_json()
        parsed = json.loads(result)
        
        expected = {
            "data": "Hello World",
            "type": "text",
            "timestamp": timestamp,
            "client_id": "test_client"
        }
        
        assert parsed == expected

    def test_websocket_message_to_json_json_type(self):
        """Test WebSocketMessage to_json conversion for JSON type"""
        json_data = {"message": "test", "count": 5}
        message = WebSocketMessage(
            data=json_data,
            message_type="json"
        )
        
        result = message.to_json()
        parsed = json.loads(result)
        
        assert parsed == json_data

    def test_websocket_message_to_json_binary_type_error(self):
        """Test WebSocketMessage to_json conversion error for binary type"""
        message = WebSocketMessage(
            data=b"binary data",
            message_type="binary"
        )
        
        with pytest.raises(ValueError, match="Cannot convert binary message to JSON"):
            message.to_json()

    def test_websocket_message_to_json_minimal(self):
        """Test WebSocketMessage to_json conversion with minimal fields"""
        message = WebSocketMessage(data="test message")
        
        result = message.to_json()
        parsed = json.loads(result)
        
        assert parsed["data"] == "test message"
        assert parsed["type"] == "text"
        assert isinstance(parsed["timestamp"], float)
        assert parsed["client_id"] is None


class TestWebSocketHandler:
    """Test WebSocketHandler class"""

    def test_websocket_handler_init_default_config(self):
        """Test WebSocketHandler initialization with default config"""
        handler = WebSocketHandler()
        
        assert isinstance(handler.config, WebSocketConfig)
        assert handler.config.host == "localhost"
        assert handler.config.port == 8765
        assert handler.clients == set()
        assert handler._message_handlers == {}
        assert handler._stream_processor is None
        assert handler.is_running is False

    def test_websocket_handler_init_custom_config(self):
        """Test WebSocketHandler initialization with custom config"""
        custom_config = WebSocketConfig(host="example.com", port=9001)
        handler = WebSocketHandler(custom_config)
        
        assert handler.config is custom_config
        assert handler.config.host == "example.com"
        assert handler.config.port == 9001

    def test_set_stream_processor(self):
        """Test setting stream processor"""
        handler = WebSocketHandler()
        mock_processor = Mock()
        
        handler.set_stream_processor(mock_processor)
        
        assert handler._stream_processor is mock_processor

    def test_websocket_handler_clients_set(self):
        """Test that clients is a set and can be modified"""
        handler = WebSocketHandler()
        
        # Initially empty
        assert len(handler.clients) == 0
        
        # Can add mock clients
        mock_client1 = Mock()
        mock_client2 = Mock()
        
        handler.clients.add(mock_client1)
        handler.clients.add(mock_client2)
        
        assert len(handler.clients) == 2
        assert mock_client1 in handler.clients
        assert mock_client2 in handler.clients

    def test_websocket_handler_message_handlers(self):
        """Test message handlers dictionary"""
        handler = WebSocketHandler()
        
        # Initially empty
        assert len(handler._message_handlers) == 0
        
        # Can add handlers
        handler._message_handlers["test_message"] = Mock()
        handler._message_handlers["another_message"] = Mock()
        
        assert len(handler._message_handlers) == 2
        assert "test_message" in handler._message_handlers
        assert "another_message" in handler._message_handlers

    def test_websocket_handler_attributes_exist(self):
        """Test that WebSocketHandler has expected attributes"""
        handler = WebSocketHandler()
        
        # Check all expected attributes exist
        assert hasattr(handler, 'config')
        assert hasattr(handler, 'clients')
        assert hasattr(handler, '_message_handlers')
        assert hasattr(handler, '_stream_processor')
        assert hasattr(handler, 'is_running')

    @patch('strataregula.protocols.websocket.WEBSOCKETS_AVAILABLE', False)
    def test_websocket_handler_without_websockets_library(self):
        """Test WebSocketHandler behavior when websockets library is not available"""
        # Should still be able to create handler
        handler = WebSocketHandler()
        
        # Basic functionality should work
        assert isinstance(handler.config, WebSocketConfig)
        
        mock_processor = Mock()
        handler.set_stream_processor(mock_processor)
        assert handler._stream_processor is mock_processor

    def test_websocket_config_ssl_context(self):
        """Test WebSocketConfig with SSL context"""
        ssl_context = ssl.create_default_context()
        config = WebSocketConfig(ssl_context=ssl_context)
        
        assert config.ssl_context is ssl_context

    def test_websocket_config_compression_options(self):
        """Test WebSocketConfig compression options"""
        # Test with deflate compression
        config1 = WebSocketConfig(compression="deflate")
        assert config1.compression == "deflate"
        
        # Test with no compression
        config2 = WebSocketConfig(compression=None)
        assert config2.compression is None

    def test_websocket_config_size_limits(self):
        """Test WebSocketConfig size and queue limits"""
        config = WebSocketConfig(
            max_size=5 * 1024 * 1024,  # 5MB
            max_queue=128
        )
        
        assert config.max_size == 5 * 1024 * 1024
        assert config.max_queue == 128

    def test_websocket_config_timeouts(self):
        """Test WebSocketConfig timeout settings"""
        config = WebSocketConfig(
            ping_interval=45.0,
            ping_timeout=30.0,
            close_timeout=15.0
        )
        
        assert config.ping_interval == 45.0
        assert config.ping_timeout == 30.0
        assert config.close_timeout == 15.0

    def test_websocket_message_different_data_types(self):
        """Test WebSocketMessage with different data types"""
        # String data
        msg1 = WebSocketMessage(data="string data", message_type="text")
        assert msg1.data == "string data"
        
        # Binary data
        msg2 = WebSocketMessage(data=b"binary", message_type="binary")
        assert msg2.data == b"binary"
        
        # Dictionary data (for JSON)
        msg3 = WebSocketMessage(data={"key": "value"}, message_type="json")
        assert msg3.data == {"key": "value"}
        
        # List data (for JSON)
        msg4 = WebSocketMessage(data=[1, 2, 3], message_type="json")
        assert msg4.data == [1, 2, 3]

    def test_websocket_message_client_id_variations(self):
        """Test WebSocketMessage with different client ID formats"""
        # UUID-like client ID
        msg1 = WebSocketMessage(data="test", client_id="550e8400-e29b-41d4-a716-446655440000")
        assert msg1.client_id == "550e8400-e29b-41d4-a716-446655440000"
        
        # Simple numeric client ID
        msg2 = WebSocketMessage(data="test", client_id="12345")
        assert msg2.client_id == "12345"
        
        # Descriptive client ID
        msg3 = WebSocketMessage(data="test", client_id="user_session_abc123")
        assert msg3.client_id == "user_session_abc123"