"""
Raw Log Broadcaster Service
Manages WebSocket connections and broadcasts raw log lines to subscribed clients.
"""
import json
import threading
from datetime import datetime
from typing import Dict, Set, Optional
from fastapi import WebSocket
import asyncio
from concurrent.futures import ThreadPoolExecutor


class RawLogBroadcaster:
    """
    Thread-safe broadcaster for raw log lines via WebSocket.
    Manages connections and subscriptions per log source.
    """
    
    def __init__(self):
        # Dictionary: connection_id -> WebSocket
        self.connections: Dict[str, WebSocket] = {}
        # Dictionary: connection_id -> Set of subscribed log sources
        self.subscriptions: Dict[str, Set[str]] = {}
        # Lock for thread-safe operations
        self.lock = threading.Lock()
        # Connection counter for unique IDs
        self.connection_counter = 0
        # Event loop for async operations from sync threads
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        # Thread pool executor for running async code from sync threads
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="broadcaster")
    
    def add_connection(self, websocket: WebSocket) -> str:
        """Add a new WebSocket connection and return its ID"""
        with self.lock:
            self.connection_counter += 1
            connection_id = f"conn_{self.connection_counter}"
            self.connections[connection_id] = websocket
            self.subscriptions[connection_id] = set()
            print(f"✓ WebSocket connection added: {connection_id} (Total: {len(self.connections)})")
            return connection_id
    
    def remove_connection(self, connection_id: str):
        """Remove a WebSocket connection"""
        with self.lock:
            if connection_id in self.connections:
                del self.connections[connection_id]
            if connection_id in self.subscriptions:
                del self.subscriptions[connection_id]
            print(f"✓ WebSocket connection removed: {connection_id} (Total: {len(self.connections)})")
    
    def subscribe(self, connection_id: str, log_source: str):
        """Subscribe a connection to a log source"""
        with self.lock:
            if connection_id in self.subscriptions:
                self.subscriptions[connection_id].add(log_source)
                print(f"✓ Connection {connection_id} subscribed to {log_source}")
    
    def unsubscribe(self, connection_id: str, log_source: str):
        """Unsubscribe a connection from a log source"""
        with self.lock:
            if connection_id in self.subscriptions:
                self.subscriptions[connection_id].discard(log_source)
                print(f"✓ Connection {connection_id} unsubscribed from {log_source}")
    
    def is_subscribed(self, connection_id: str, log_source: str) -> bool:
        """Check if a connection is subscribed to a log source"""
        with self.lock:
            if connection_id in self.subscriptions:
                return log_source in self.subscriptions[connection_id] or "all" in self.subscriptions[connection_id]
            return False
    
    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the event loop for async operations"""
        self.loop = loop
    
    async def _broadcast_async(self, log_source: str, raw_line: str):
        """
        Internal async method to broadcast a raw log line.
        """
        if not raw_line or not raw_line.strip():
            return
        
        # Create message payload
        message = {
            "type": "raw_log",
            "log_source": log_source,
            "raw_line": raw_line.strip(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        message_json = json.dumps(message)
        
        # Get list of connections to send to (with lock)
        connections_to_send = []
        with self.lock:
            for conn_id, subscriptions in self.subscriptions.items():
                if "all" in subscriptions or log_source in subscriptions:
                    if conn_id in self.connections:
                        connections_to_send.append(conn_id)
        
        # Send to all subscribed connections (without holding lock)
        disconnected = []
        for conn_id in connections_to_send:
            try:
                websocket = self.connections.get(conn_id)
                if websocket:
                    await websocket.send_text(message_json)
            except Exception as e:
                print(f"✗ Error sending to {conn_id}: {e}")
                disconnected.append(conn_id)
        
        # Remove disconnected connections
        if disconnected:
            with self.lock:
                for conn_id in disconnected:
                    self.remove_connection(conn_id)
    
    def broadcast(self, log_source: str, raw_line: str):
        """
        Broadcast a raw log line to all subscribed connections.
        This is a synchronous wrapper that can be called from log ingestion threads.
        """
        if not raw_line or not raw_line.strip():
            return
        
        # If we have an event loop, schedule the async broadcast
        if self.loop and self.loop.is_running():
            try:
                # Use call_soon_threadsafe to schedule from any thread
                asyncio.run_coroutine_threadsafe(
                    self._broadcast_async(log_source, raw_line),
                    self.loop
                )
            except Exception as e:
                print(f"✗ Error scheduling broadcast: {e}")
        else:
            # Fallback: run in executor if no loop available
            try:
                future = self.executor.submit(
                    lambda: asyncio.run(self._broadcast_async(log_source, raw_line))
                )
            except Exception as e:
                print(f"✗ Error broadcasting log: {e}")
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        with self.lock:
            return len(self.connections)


# Global singleton instance
raw_log_broadcaster = RawLogBroadcaster()

