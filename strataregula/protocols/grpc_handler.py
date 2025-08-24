"""
gRPC protocol handler for high-performance RPC communication.
Provides gRPC server and client implementations with stream processing integration.
"""

import asyncio
import logging
import time
from typing import Optional, Callable, Dict, Any, AsyncIterator, Iterator
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)

# Optional grpcio imports
try:
    import grpc
    from grpc import aio as grpc_aio
    import grpc.reflection.v1alpha.reflection_pb2_grpc as reflection_grpc
    import grpc.reflection.v1alpha.reflection_pb2 as reflection_pb2
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    logger.info("grpcio not available, gRPC functionality disabled")


@dataclass
class GRPCConfig:
    """Configuration for gRPC connections."""
    host: str = "localhost"
    port: int = 50051
    max_workers: int = 10
    max_send_message_length: int = 4 * 1024 * 1024  # 4MB
    max_receive_message_length: int = 4 * 1024 * 1024  # 4MB
    keepalive_time_ms: int = 30000
    keepalive_timeout_ms: int = 5000
    keepalive_permit_without_calls: bool = True
    http2_max_pings_without_data: int = 0
    http2_min_sent_ping_interval_without_data_ms: int = 300000
    http2_min_ping_interval_without_data_ms: int = 300000
    compression: Optional[str] = None  # gzip, deflate
    ssl_credentials: Optional[Any] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GRPCMessage:
    """gRPC message wrapper for stream processing."""
    data: Any
    method_name: str
    metadata: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    client_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "data": self.data,
            "method": self.method_name,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "client_id": self.client_id
        }


class GRPCHandler:
    """Base gRPC handler with stream processing integration."""
    
    def __init__(self, config: Optional[GRPCConfig] = None):
        self.config = config or GRPCConfig()
        self._service_handlers: Dict[str, Callable] = {}
        self._stream_processor = None
        self._interceptors = []
        self.is_running = False
    
    def set_stream_processor(self, processor):
        """Set stream processor for message processing."""
        self._stream_processor = processor
    
    def register_service_handler(self, method_name: str, handler: Callable) -> None:
        """Register a handler for specific gRPC methods."""
        self._service_handlers[method_name] = handler
    
    def add_interceptor(self, interceptor) -> None:
        """Add gRPC interceptor."""
        self._interceptors.append(interceptor)
    
    async def process_unary_request(self, method_name: str, request, context) -> Any:
        """Process unary gRPC request."""
        try:
            # Create message wrapper
            grpc_message = GRPCMessage(
                data=request,
                method_name=method_name,
                client_id=str(id(context))
            )
            
            # Process with stream processor if available
            if self._stream_processor:
                # Convert request to processable format
                data_str = str(request) if not hasattr(request, 'SerializeToString') else request.SerializeToString().decode('utf-8', errors='ignore')
                
                # Register processor for this method if not exists
                processor_name = f"grpc_{method_name}"
                if processor_name not in self._stream_processor.chunk_processor._processors:
                    self._stream_processor.register_processor(
                        processor_name,
                        lambda chunk: self._default_grpc_processor(chunk, method_name)
                    )
                
                results = list(self._stream_processor.chunk_processor.process_chunks(
                    data_str, processor_name
                ))
                
                # Use first result or default response
                if results:
                    return results[0]
            
            # Handle with registered handlers
            handler = self._service_handlers.get(method_name)
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    return await handler(grpc_message, context)
                else:
                    return handler(grpc_message, context)
            
            # Default response
            return self._create_default_response(method_name, request)
            
        except Exception as e:
            logger.error(f"Error processing gRPC request {method_name}: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            raise
    
    async def process_stream_request(self, method_name: str, request_iterator, context) -> AsyncIterator[Any]:
        """Process streaming gRPC request."""
        try:
            async for request in request_iterator:
                result = await self.process_unary_request(method_name, request, context)
                if result:
                    yield result
        except Exception as e:
            logger.error(f"Error processing gRPC stream {method_name}: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            raise
    
    def _default_grpc_processor(self, chunk: str, method_name: str) -> Dict[str, Any]:
        """Default processor for gRPC chunks."""
        return {
            "processed_chunk": chunk[:100] + "..." if len(chunk) > 100 else chunk,
            "method": method_name,
            "length": len(chunk),
            "timestamp": time.time()
        }
    
    def _create_default_response(self, method_name: str, request) -> Dict[str, Any]:
        """Create default response for unhandled methods."""
        return {
            "status": "processed",
            "method": method_name,
            "timestamp": time.time(),
            "message": f"Processed {method_name} request"
        }


class GRPCServer(GRPCHandler):
    """gRPC server implementation."""
    
    def __init__(self, config: Optional[GRPCConfig] = None):
        super().__init__(config)
        self.server: Optional[grpc_aio.Server] = None
        self._services = []
    
    def add_generic_service(self, service_class, service_implementation):
        """Add a generic gRPC service."""
        if not GRPC_AVAILABLE:
            raise RuntimeError("grpcio not available")
        
        self._services.append((service_class, service_implementation))
    
    async def start_server(self) -> None:
        """Start the gRPC server."""
        if not GRPC_AVAILABLE:
            raise RuntimeError("grpcio not available")
        
        logger.info(f"Starting gRPC server on {self.config.host}:{self.config.port}")
        
        # Create server with options
        options = [
            ('grpc.keepalive_time_ms', self.config.keepalive_time_ms),
            ('grpc.keepalive_timeout_ms', self.config.keepalive_timeout_ms),
            ('grpc.keepalive_permit_without_calls', self.config.keepalive_permit_without_calls),
            ('grpc.http2.max_pings_without_data', self.config.http2_max_pings_without_data),
            ('grpc.http2.min_sent_ping_interval_without_data_ms', self.config.http2_min_sent_ping_interval_without_data_ms),
            ('grpc.http2.min_ping_interval_without_data_ms', self.config.http2_min_ping_interval_without_data_ms),
            ('grpc.max_send_message_length', self.config.max_send_message_length),
            ('grpc.max_receive_message_length', self.config.max_receive_message_length),
        ]
        
        # Add custom options
        options.extend([(k, v) for k, v in self.config.options.items()])
        
        self.server = grpc_aio.server(
            interceptors=self._interceptors,
            options=options
        )
        
        # Add registered services
        for service_class, service_impl in self._services:
            service_class.add_to_server(service_impl, self.server)
        
        # Add reflection service for debugging
        reflection_grpc.add_ReflectionServicer_to_server(
            reflection_grpc.ReflectionServicer(), self.server
        )
        
        # Configure listening address
        listen_addr = f"{self.config.host}:{self.config.port}"
        if self.config.ssl_credentials:
            self.server.add_secure_port(listen_addr, self.config.ssl_credentials)
        else:
            self.server.add_insecure_port(listen_addr)
        
        # Start server
        await self.server.start()
        self.is_running = True
        logger.info(f"gRPC server started on {listen_addr}")
    
    async def stop_server(self, grace_period: float = 5.0) -> None:
        """Stop the gRPC server."""
        if self.server and self.is_running:
            logger.info("Stopping gRPC server")
            await self.server.stop(grace_period)
            self.is_running = False
            logger.info("gRPC server stopped")
    
    async def run_forever(self) -> None:
        """Run the server until interrupted."""
        await self.start_server()
        try:
            await self.server.wait_for_termination()
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        finally:
            await self.stop_server()


class GRPCClient(GRPCHandler):
    """gRPC client implementation."""
    
    def __init__(self, target: str, config: Optional[GRPCConfig] = None):
        super().__init__(config)
        self.target = target
        self.channel: Optional[grpc_aio.Channel] = None
        self._stubs: Dict[str, Any] = {}
    
    async def connect(self) -> None:
        """Connect to gRPC server."""
        if not GRPC_AVAILABLE:
            raise RuntimeError("grpcio not available")
        
        logger.info(f"Connecting to gRPC server at {self.target}")
        
        # Configure channel options
        options = [
            ('grpc.keepalive_time_ms', self.config.keepalive_time_ms),
            ('grpc.keepalive_timeout_ms', self.config.keepalive_timeout_ms),
            ('grpc.keepalive_permit_without_calls', self.config.keepalive_permit_without_calls),
            ('grpc.max_send_message_length', self.config.max_send_message_length),
            ('grpc.max_receive_message_length', self.config.max_receive_message_length),
        ]
        
        # Add custom options
        options.extend([(k, v) for k, v in self.config.options.items()])
        
        # Create channel
        if self.config.ssl_credentials:
            self.channel = grpc_aio.secure_channel(
                self.target, 
                self.config.ssl_credentials,
                options=options
            )
        else:
            self.channel = grpc_aio.insecure_channel(
                self.target,
                options=options
            )
        
        self.is_running = True
        logger.info("Connected to gRPC server")
    
    async def disconnect(self) -> None:
        """Disconnect from gRPC server."""
        if self.channel:
            logger.info("Disconnecting from gRPC server")
            await self.channel.close()
            self.channel = None
            self.is_running = False
            self._stubs.clear()
            logger.info("Disconnected from gRPC server")
    
    def register_stub(self, name: str, stub_class) -> None:
        """Register a gRPC stub for making calls."""
        if not self.channel:
            raise RuntimeError("Not connected to server")
        
        self._stubs[name] = stub_class(self.channel)
    
    def get_stub(self, name: str):
        """Get registered stub."""
        return self._stubs.get(name)
    
    async def call_unary(self, stub_name: str, method_name: str, request, 
                        timeout: Optional[float] = None, metadata=None) -> Any:
        """Make unary gRPC call."""
        if not self.is_running:
            raise RuntimeError("Not connected to server")
        
        stub = self._stubs.get(stub_name)
        if not stub:
            raise ValueError(f"Stub '{stub_name}' not registered")
        
        method = getattr(stub, method_name, None)
        if not method:
            raise ValueError(f"Method '{method_name}' not found in stub '{stub_name}'")
        
        try:
            # Process request with stream processor if available
            if self._stream_processor:
                processor_name = f"grpc_client_{method_name}"
                if processor_name not in self._stream_processor.chunk_processor._processors:
                    self._stream_processor.register_processor(
                        processor_name,
                        lambda chunk: {"processed": chunk, "method": method_name}
                    )
            
            response = await method(request, timeout=timeout, metadata=metadata)
            return response
            
        except grpc.RpcError as e:
            logger.error(f"gRPC call failed: {e}")
            raise
    
    async def call_stream(self, stub_name: str, method_name: str, request_iterator,
                         timeout: Optional[float] = None, metadata=None) -> AsyncIterator[Any]:
        """Make streaming gRPC call."""
        if not self.is_running:
            raise RuntimeError("Not connected to server")
        
        stub = self._stubs.get(stub_name)
        if not stub:
            raise ValueError(f"Stub '{stub_name}' not registered")
        
        method = getattr(stub, method_name, None)
        if not method:
            raise ValueError(f"Method '{method_name}' not found in stub '{stub_name}'")
        
        try:
            async for response in method(request_iterator, timeout=timeout, metadata=metadata):
                yield response
                
        except grpc.RpcError as e:
            logger.error(f"gRPC streaming call failed: {e}")
            raise
    
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self.channel is not None and self.is_running