"""
Tests for protocols grpc_handler module
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from dataclasses import FrozenInstanceError

from strataregula.protocols.grpc_handler import (
    GRPCConfig, GRPCMessage, GRPCHandler, GRPC_AVAILABLE
)


class TestGRPCConfig:
    """Test GRPCConfig dataclass"""

    def test_grpc_config_defaults(self):
        """Test GRPCConfig creation with default values"""
        config = GRPCConfig()
        
        assert config.host == "localhost"
        assert config.port == 50051
        assert config.max_workers == 10
        assert config.max_send_message_length == 4 * 1024 * 1024
        assert config.max_receive_message_length == 4 * 1024 * 1024
        assert config.keepalive_time_ms == 30000
        assert config.keepalive_timeout_ms == 5000
        assert config.keepalive_permit_without_calls is True
        assert config.http2_max_pings_without_data == 0
        assert config.http2_min_sent_ping_interval_without_data_ms == 300000
        assert config.http2_min_ping_interval_without_data_ms == 300000
        assert config.compression is None
        assert config.ssl_credentials is None
        assert config.options == {}

    def test_grpc_config_custom_values(self):
        """Test GRPCConfig creation with custom values"""
        custom_options = {"custom_option": "value"}
        
        config = GRPCConfig(
            host="example.com",
            port=9999,
            max_workers=20,
            compression="gzip",
            options=custom_options
        )
        
        assert config.host == "example.com"
        assert config.port == 9999
        assert config.max_workers == 20
        assert config.compression == "gzip"
        assert config.options == custom_options

    def test_grpc_config_options_default_factory(self):
        """Test that options dict is created as new instance for each config"""
        config1 = GRPCConfig()
        config2 = GRPCConfig()
        
        # Modify one config's options
        config1.options["test"] = "value"
        
        # Other config should not be affected
        assert "test" not in config2.options


class TestGRPCMessage:
    """Test GRPCMessage dataclass"""

    def test_grpc_message_creation(self):
        """Test GRPCMessage creation with required fields"""
        message = GRPCMessage(
            data={"test": "data"},
            method_name="TestMethod"
        )
        
        assert message.data == {"test": "data"}
        assert message.method_name == "TestMethod"
        assert message.metadata == {}
        assert isinstance(message.timestamp, float)
        assert message.client_id is None

    def test_grpc_message_with_all_fields(self):
        """Test GRPCMessage creation with all fields"""
        metadata = {"header": "value"}
        timestamp = time.time()
        
        message = GRPCMessage(
            data="test_data",
            method_name="TestMethod",
            metadata=metadata,
            timestamp=timestamp,
            client_id="client123"
        )
        
        assert message.data == "test_data"
        assert message.method_name == "TestMethod"
        assert message.metadata == metadata
        assert message.timestamp == timestamp
        assert message.client_id == "client123"

    def test_grpc_message_metadata_default_factory(self):
        """Test that metadata dict is created as new instance for each message"""
        message1 = GRPCMessage(data="data1", method_name="method1")
        message2 = GRPCMessage(data="data2", method_name="method2")
        
        # Modify one message's metadata
        message1.metadata["test"] = "value"
        
        # Other message should not be affected
        assert "test" not in message2.metadata

    def test_grpc_message_to_dict(self):
        """Test GRPCMessage to_dict conversion"""
        metadata = {"header": "value"}
        timestamp = 1234567890.0
        
        message = GRPCMessage(
            data={"test": "data"},
            method_name="TestMethod",
            metadata=metadata,
            timestamp=timestamp,
            client_id="client123"
        )
        
        result = message.to_dict()
        
        expected = {
            "data": {"test": "data"},
            "method": "TestMethod",
            "metadata": metadata,
            "timestamp": timestamp,
            "client_id": "client123"
        }
        
        assert result == expected

    def test_grpc_message_to_dict_minimal(self):
        """Test GRPCMessage to_dict conversion with minimal fields"""
        message = GRPCMessage(
            data="simple_data",
            method_name="SimpleMethod"
        )
        
        result = message.to_dict()
        
        assert result["data"] == "simple_data"
        assert result["method"] == "SimpleMethod"
        assert result["metadata"] == {}
        assert isinstance(result["timestamp"], float)
        assert result["client_id"] is None


class TestGRPCHandler:
    """Test GRPCHandler class"""

    def test_grpc_handler_init_default_config(self):
        """Test GRPCHandler initialization with default config"""
        handler = GRPCHandler()
        
        assert isinstance(handler.config, GRPCConfig)
        assert handler.config.host == "localhost"
        assert handler.config.port == 50051
        assert handler._service_handlers == {}
        assert handler._stream_processor is None
        assert handler._interceptors == []
        assert handler.is_running is False

    def test_grpc_handler_init_custom_config(self):
        """Test GRPCHandler initialization with custom config"""
        custom_config = GRPCConfig(host="example.com", port=9999)
        handler = GRPCHandler(custom_config)
        
        assert handler.config is custom_config
        assert handler.config.host == "example.com"
        assert handler.config.port == 9999

    def test_set_stream_processor(self):
        """Test setting stream processor"""
        handler = GRPCHandler()
        mock_processor = Mock()
        
        handler.set_stream_processor(mock_processor)
        
        assert handler._stream_processor is mock_processor

    def test_register_service_handler(self):
        """Test registering service handler"""
        handler = GRPCHandler()
        mock_handler_func = Mock()
        
        handler.register_service_handler("TestMethod", mock_handler_func)
        
        assert "TestMethod" in handler._service_handlers
        assert handler._service_handlers["TestMethod"] is mock_handler_func

    def test_register_multiple_service_handlers(self):
        """Test registering multiple service handlers"""
        handler = GRPCHandler()
        handler1 = Mock()
        handler2 = Mock()
        
        handler.register_service_handler("Method1", handler1)
        handler.register_service_handler("Method2", handler2)
        
        assert len(handler._service_handlers) == 2
        assert handler._service_handlers["Method1"] is handler1
        assert handler._service_handlers["Method2"] is handler2

    def test_grpc_handler_attributes_exist(self):
        """Test that GRPCHandler has expected attributes"""
        handler = GRPCHandler()
        
        # Check all expected attributes exist
        assert hasattr(handler, 'config')
        assert hasattr(handler, '_service_handlers')
        assert hasattr(handler, '_stream_processor')
        assert hasattr(handler, '_interceptors')
        assert hasattr(handler, 'is_running')

    @patch('strataregula.protocols.grpc_handler.GRPC_AVAILABLE', False)
    def test_grpc_handler_without_grpc_library(self):
        """Test GRPCHandler behavior when grpcio is not available"""
        # Should still be able to create handler
        handler = GRPCHandler()
        
        # Basic functionality should work
        assert isinstance(handler.config, GRPCConfig)
        
        mock_processor = Mock()
        handler.set_stream_processor(mock_processor)
        assert handler._stream_processor is mock_processor

    def test_grpc_config_message_size_limits(self):
        """Test GRPCConfig message size limit settings"""
        config = GRPCConfig(
            max_send_message_length=8 * 1024 * 1024,  # 8MB
            max_receive_message_length=16 * 1024 * 1024  # 16MB
        )
        
        assert config.max_send_message_length == 8 * 1024 * 1024
        assert config.max_receive_message_length == 16 * 1024 * 1024

    def test_grpc_config_keepalive_settings(self):
        """Test GRPCConfig keepalive settings"""
        config = GRPCConfig(
            keepalive_time_ms=60000,  # 1 minute
            keepalive_timeout_ms=10000,  # 10 seconds
            keepalive_permit_without_calls=False
        )
        
        assert config.keepalive_time_ms == 60000
        assert config.keepalive_timeout_ms == 10000
        assert config.keepalive_permit_without_calls is False

    def test_grpc_config_http2_settings(self):
        """Test GRPCConfig HTTP/2 specific settings"""
        config = GRPCConfig(
            http2_max_pings_without_data=10,
            http2_min_sent_ping_interval_without_data_ms=600000,
            http2_min_ping_interval_without_data_ms=600000
        )
        
        assert config.http2_max_pings_without_data == 10
        assert config.http2_min_sent_ping_interval_without_data_ms == 600000
        assert config.http2_min_ping_interval_without_data_ms == 600000

    def test_grpc_message_timestamp_auto_generation(self):
        """Test that GRPCMessage automatically generates timestamp"""
        before = time.time()
        message = GRPCMessage(data="test", method_name="test")
        after = time.time()
        
        assert before <= message.timestamp <= after

    def test_grpc_message_immutability_after_creation(self):
        """Test that we can modify GRPCMessage attributes after creation"""
        message = GRPCMessage(data="test", method_name="test")
        
        # Should be able to modify attributes (dataclass is not frozen)
        message.client_id = "new_client"
        assert message.client_id == "new_client"
        
        # Should be able to modify nested objects
        message.metadata["new_key"] = "new_value"
        assert message.metadata["new_key"] == "new_value"