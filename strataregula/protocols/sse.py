"""
Server-Sent Events (SSE) protocol handler for HTTP/2 server-side event streaming.
Provides SSE server implementation with stream processing integration.
"""

import asyncio
import json
import time
import logging
from typing import Optional, Callable, Dict, Any, Set, AsyncIterator, Union
from dataclasses import dataclass, field
from urllib.parse import parse_qs
import uuid

logger = logging.getLogger(__name__)

# Optional aiohttp import for HTTP server
try:
    from aiohttp import web, WSMsgType
    from aiohttp.web_request import Request
    from aiohttp.web_response import StreamResponse
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.info("aiohttp not available, SSE functionality disabled")


@dataclass
class SSEConfig:
    """Configuration for SSE server."""
    host: str = "localhost"
    port: int = 8080
    path: str = "/events"
    keepalive_interval: float = 30.0  # Send keepalive every 30 seconds
    retry_time: int = 3000  # Client retry time in milliseconds
    cors_origins: Set[str] = field(default_factory=lambda: {"*"})
    max_connections: int = 1000
    buffer_size: int = 1024
    compression: bool = True


@dataclass
class SSEEvent:
    """Server-Sent Event data structure."""
    data: Union[str, Dict[str, Any]]
    event_type: Optional[str] = None
    event_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    retry: Optional[int] = None
    timestamp: float = field(default_factory=time.time)
    
    def format(self) -> str:
        """Format event for SSE transmission."""
        lines = []
        
        # Add event type
        if self.event_type:
            lines.append(f"event: {self.event_type}")
        
        # Add event ID
        if self.event_id:
            lines.append(f"id: {self.event_id}")
        
        # Add retry time
        if self.retry:
            lines.append(f"retry: {self.retry}")
        
        # Add data
        data_str = json.dumps(self.data) if isinstance(self.data, dict) else str(self.data)
        for line in data_str.splitlines():
            lines.append(f"data: {line}")
        
        # End with double newline
        lines.append("")
        lines.append("")
        
        return "\n".join(lines)


class SSEConnection:
    """Represents an active SSE connection."""
    
    def __init__(self, response: StreamResponse, client_id: str, query_params: Dict[str, str]):
        self.response = response
        self.client_id = client_id
        self.query_params = query_params
        self.connected_at = time.time()
        self.last_activity = time.time()
        self.events_sent = 0
        self.is_active = True
    
    async def send_event(self, event: SSEEvent) -> bool:
        """Send event to client. Returns False if connection is broken."""
        try:
            await self.response.write(event.format().encode('utf-8'))
            await self.response.drain()
            
            self.last_activity = time.time()
            self.events_sent += 1
            return True
            
        except Exception as e:
            logger.warning(f"Failed to send event to client {self.client_id}: {e}")
            self.is_active = False
            return False
    
    async def send_keepalive(self) -> bool:
        """Send keepalive comment."""
        try:
            keepalive = f": keepalive {int(time.time())}\n\n"
            await self.response.write(keepalive.encode('utf-8'))
            await self.response.drain()
            
            self.last_activity = time.time()
            return True
            
        except Exception as e:
            logger.warning(f"Failed to send keepalive to client {self.client_id}: {e}")
            self.is_active = False
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "client_id": self.client_id,
            "connected_at": self.connected_at,
            "duration": time.time() - self.connected_at,
            "last_activity": self.last_activity,
            "events_sent": self.events_sent,
            "is_active": self.is_active,
            "query_params": self.query_params
        }


class SSEHandler:
    """Base SSE handler with stream processing integration."""
    
    def __init__(self, config: Optional[SSEConfig] = None):
        self.config = config or SSEConfig()
        self.connections: Dict[str, SSEConnection] = {}
        self._event_handlers: Dict[str, Callable] = {}
        self._stream_processor = None
        self.is_running = False
        self._keepalive_task: Optional[asyncio.Task] = None
    
    def set_stream_processor(self, processor):
        """Set stream processor for event processing."""
        self._stream_processor = processor
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register handler for specific event types."""
        self._event_handlers[event_type] = handler
    
    async def handle_connection(self, request: Request) -> StreamResponse:
        """Handle new SSE connection."""
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp not available")
        
        # Check connection limit
        if len(self.connections) >= self.config.max_connections:
            return web.Response(
                text="Too many connections",
                status=503,
                headers={"Retry-After": "60"}
            )
        
        # Create client ID
        client_id = str(uuid.uuid4())
        
        # Parse query parameters
        query_params = dict(request.query)
        
        logger.info(f"New SSE connection from {request.remote}, client_id: {client_id}")
        
        # Create response
        response = web.StreamResponse(
            status=200,
            reason='OK',
            headers={
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',  # Disable nginx buffering
            }
        )
        
        # Add CORS headers
        if self.config.cors_origins:
            origin = request.headers.get('Origin', '*')
            if '*' in self.config.cors_origins or origin in self.config.cors_origins:
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        await response.prepare(request)
        
        # Create connection object
        connection = SSEConnection(response, client_id, query_params)
        self.connections[client_id] = connection
        
        try:
            # Send initial connection event
            welcome_event = SSEEvent(
                data={
                    "type": "connection",
                    "client_id": client_id,
                    "timestamp": time.time(),
                    "server_time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
                },
                event_type="connection",
                retry=self.config.retry_time
            )
            await connection.send_event(welcome_event)
            
            # Handle custom connection logic
            await self._on_client_connected(connection)
            
            # Keep connection alive until client disconnects
            while connection.is_active:
                await asyncio.sleep(1)
                
                # Check if connection is still valid
                if response.transport and response.transport.is_closing():
                    break
        
        except Exception as e:
            logger.error(f"Error handling SSE connection {client_id}: {e}")
        
        finally:
            # Clean up connection
            if client_id in self.connections:
                del self.connections[client_id]
            await self._on_client_disconnected(client_id)
            logger.info(f"SSE client {client_id} disconnected")
        
        return response
    
    async def _on_client_connected(self, connection: SSEConnection) -> None:
        """Called when a client connects."""
        pass
    
    async def _on_client_disconnected(self, client_id: str) -> None:
        """Called when a client disconnects."""
        pass
    
    async def broadcast_event(self, event: SSEEvent, client_filter: Optional[Callable[[SSEConnection], bool]] = None) -> int:
        """Broadcast event to all connected clients."""
        sent_count = 0
        disconnected = []
        
        for client_id, connection in self.connections.items():
            # Apply client filter if provided
            if client_filter and not client_filter(connection):
                continue
            
            success = await connection.send_event(event)
            if success:
                sent_count += 1
            else:
                disconnected.append(client_id)
        
        # Remove disconnected clients
        for client_id in disconnected:
            if client_id in self.connections:
                del self.connections[client_id]
        
        return sent_count
    
    async def send_to_client(self, client_id: str, event: SSEEvent) -> bool:
        """Send event to specific client."""
        connection = self.connections.get(client_id)
        if connection:
            return await connection.send_event(event)
        return False
    
    async def process_with_stream(self, data: Any, event_type: str = "data") -> None:
        """Process data with stream processor and broadcast results."""
        if not self._stream_processor:
            # Just broadcast raw data
            event = SSEEvent(data=data, event_type=event_type)
            await self.broadcast_event(event)
            return
        
        # Process with stream processor
        processor_name = f"sse_{event_type}"
        if processor_name not in self._stream_processor.chunk_processor._processors:
            self._stream_processor.register_processor(
                processor_name,
                lambda chunk: {"processed": chunk, "type": event_type, "timestamp": time.time()}
            )
        
        data_str = json.dumps(data) if isinstance(data, dict) else str(data)
        results = list(self._stream_processor.chunk_processor.process_chunks(
            data_str, processor_name
        ))
        
        # Broadcast each result
        for result in results:
            event = SSEEvent(data=result, event_type=f"processed_{event_type}")
            await self.broadcast_event(event)
    
    async def start_keepalive(self) -> None:
        """Start keepalive task."""
        self._keepalive_task = asyncio.create_task(self._keepalive_loop())
    
    async def stop_keepalive(self) -> None:
        """Stop keepalive task."""
        if self._keepalive_task:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass
    
    async def _keepalive_loop(self) -> None:
        """Periodic keepalive sender."""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.keepalive_interval)
                
                disconnected = []
                for client_id, connection in self.connections.items():
                    success = await connection.send_keepalive()
                    if not success:
                        disconnected.append(client_id)
                
                # Remove disconnected clients
                for client_id in disconnected:
                    if client_id in self.connections:
                        del self.connections[client_id]
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in keepalive loop: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics for all connections."""
        return {
            "total_connections": len(self.connections),
            "connections": [conn.get_stats() for conn in self.connections.values()]
        }


class SSEServer(SSEHandler):
    """SSE server implementation using aiohttp."""
    
    def __init__(self, config: Optional[SSEConfig] = None):
        super().__init__(config)
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
    
    def setup_routes(self) -> None:
        """Setup HTTP routes."""
        if not self.app:
            return
        
        # Main SSE endpoint
        self.app.router.add_get(self.config.path, self.handle_connection)
        
        # Statistics endpoint
        self.app.router.add_get('/sse/stats', self.handle_stats)
        
        # Health check endpoint
        self.app.router.add_get('/sse/health', self.handle_health)
    
    async def handle_stats(self, request: Request) -> web.Response:
        """Handle statistics request."""
        stats = self.get_connection_stats()
        return web.json_response(stats)
    
    async def handle_health(self, request: Request) -> web.Response:
        """Handle health check request."""
        health = {
            "status": "healthy" if self.is_running else "stopped",
            "connections": len(self.connections),
            "uptime": time.time() - getattr(self, '_start_time', time.time())
        }
        return web.json_response(health)
    
    async def start_server(self) -> None:
        """Start the SSE server."""
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp not available")
        
        logger.info(f"Starting SSE server on {self.config.host}:{self.config.port}")
        
        self.app = web.Application()
        self.setup_routes()
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        self.site = web.TCPSite(
            self.runner, 
            self.config.host, 
            self.config.port
        )
        await self.site.start()
        
        self.is_running = True
        self._start_time = time.time()
        
        # Start keepalive
        await self.start_keepalive()
        
        logger.info(f"SSE server started on http://{self.config.host}:{self.config.port}{self.config.path}")
    
    async def stop_server(self) -> None:
        """Stop the SSE server."""
        if self.is_running:
            logger.info("Stopping SSE server")
            
            # Stop keepalive
            await self.stop_keepalive()
            
            # Close all connections
            for connection in list(self.connections.values()):
                connection.is_active = False
            
            # Stop server
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            
            self.is_running = False
            logger.info("SSE server stopped")
    
    async def run_forever(self) -> None:
        """Run the server until interrupted."""
        await self.start_server()
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        finally:
            await self.stop_server()