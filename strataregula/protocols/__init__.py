"""
Protocol support module for strataregula.
Handles WebSocket, gRPC, HTTP/2 SSE, and other real-time communication protocols.
"""

from .websocket import WebSocketHandler, WebSocketServer, WebSocketClient
from .grpc_handler import GRPCHandler, GRPCServer, GRPCClient
from .sse import SSEHandler, SSEServer

__all__ = [
    "WebSocketHandler", "WebSocketServer", "WebSocketClient",
    "GRPCHandler", "GRPCServer", "GRPCClient", 
    "SSEHandler", "SSEServer"
]
__version__ = "0.0.1"