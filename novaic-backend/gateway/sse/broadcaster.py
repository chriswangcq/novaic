"""
Worker SSE Broadcaster

Handles real-time event broadcasting to Worker processes using Server-Sent Events.
Workers subscribe to receive notifications about new messages, tasks, and results.

v11: Created for multi-process architecture.
"""

import asyncio
import json
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, Set, AsyncGenerator
from contextlib import asynccontextmanager

from common.utils.time import utc_now_iso


class SSEEvent(str, Enum):
    """SSE event types for Worker communication."""
    
    # New work available
    NEW_MESSAGE = "new_message"     # New user message to process
    NEW_TASK = "new_task"           # New action task (tool_call, reply, subagent)
    
    # Task lifecycle
    TASK_RESULT = "task_result"     # Task execution completed
    ROUND_COMPLETE = "round_complete"  # All mcpcalls in a round completed
    
    # System events
    HEARTBEAT = "heartbeat"         # Keep-alive ping
    WORKER_SHUTDOWN = "worker_shutdown"  # Graceful shutdown signal


@dataclass
class WorkerConnection:
    """Represents a connected Worker's SSE subscription."""
    
    worker_id: str
    queue: asyncio.Queue
    connected_at: str = field(default_factory=lambda: utc_now_iso())
    last_activity: str = field(default_factory=lambda: utc_now_iso())
    message_count: int = 0


class WorkerBroadcaster:
    """
    Manages SSE connections and broadcasts events to Worker processes.
    
    Features:
    - Connection management with automatic cleanup
    - Event broadcasting to all connected Workers
    - Heartbeat keepalive for connection health
    - Event filtering by agent/worker
    """
    
    def __init__(self, heartbeat_interval: int = 30):
        """
        Initialize the broadcaster.
        
        Args:
            heartbeat_interval: Seconds between heartbeat messages
        """
        self._connections: Dict[str, WorkerConnection] = {}
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._shutdown = False
    
    # ==================== Connection Management ====================
    
    def register(self, worker_id: str) -> asyncio.Queue:
        """
        Register a new Worker connection.
        
        Args:
            worker_id: Unique worker identifier
        
        Returns:
            Queue for receiving events
        """
        queue = asyncio.Queue(maxsize=100)
        self._connections[worker_id] = WorkerConnection(
            worker_id=worker_id,
            queue=queue,
        )
        print(f"[SSE] Worker {worker_id} connected (total: {len(self._connections)})")
        return queue
    
    def unregister(self, worker_id: str) -> None:
        """
        Unregister a Worker connection.
        
        Args:
            worker_id: Worker identifier to remove
        """
        if worker_id in self._connections:
            del self._connections[worker_id]
            print(f"[SSE] Worker {worker_id} disconnected (total: {len(self._connections)})")
    
    @asynccontextmanager
    async def subscribe(self, worker_id: Optional[str] = None):
        """
        Context manager for Worker subscription.
        
        Usage:
            async with broadcaster.subscribe() as queue:
                async for event in queue_generator(queue):
                    process(event)
        
        Args:
            worker_id: Optional worker ID (auto-generated if not provided)
        
        Yields:
            Tuple of (worker_id, queue)
        """
        if worker_id is None:
            worker_id = f"worker-{uuid.uuid4().hex[:8]}"
        
        queue = self.register(worker_id)
        try:
            yield worker_id, queue
        finally:
            self.unregister(worker_id)
    
    def get_connection_count(self) -> int:
        """Get number of connected Workers."""
        return len(self._connections)
    
    def get_connections(self) -> Dict[str, Dict[str, Any]]:
        """Get info about all connections."""
        return {
            wid: {
                "worker_id": conn.worker_id,
                "connected_at": conn.connected_at,
                "last_activity": conn.last_activity,
                "message_count": conn.message_count,
            }
            for wid, conn in self._connections.items()
        }
    
    # ==================== Event Broadcasting ====================
    
    async def broadcast(
        self,
        event_type: SSEEvent,
        data: Dict[str, Any],
        exclude_workers: Optional[Set[str]] = None,
    ) -> int:
        """
        Broadcast an event to all connected Workers.
        
        Args:
            event_type: Type of event
            data: Event data
            exclude_workers: Worker IDs to exclude from broadcast
        
        Returns:
            Number of Workers that received the event
        """
        if self._shutdown:
            return 0
        
        exclude = exclude_workers or set()
        event = {
            "event": event_type.value,
            "data": data,
            "timestamp": utc_now_iso(),
        }
        
        sent_count = 0
        for worker_id, conn in list(self._connections.items()):
            if worker_id in exclude:
                continue
            
            try:
                conn.queue.put_nowait(event)
                conn.message_count += 1
                conn.last_activity = utc_now_iso()
                sent_count += 1
            except asyncio.QueueFull:
                print(f"[SSE] Worker {worker_id} queue full, dropping event")
        
        return sent_count
    
    async def send_to_worker(
        self,
        worker_id: str,
        event_type: SSEEvent,
        data: Dict[str, Any],
    ) -> bool:
        """
        Send an event to a specific Worker.
        
        Args:
            worker_id: Target worker ID
            event_type: Type of event
            data: Event data
        
        Returns:
            True if sent successfully
        """
        if worker_id not in self._connections:
            return False
        
        conn = self._connections[worker_id]
        event = {
            "event": event_type.value,
            "data": data,
            "timestamp": utc_now_iso(),
        }
        
        try:
            conn.queue.put_nowait(event)
            conn.message_count += 1
            conn.last_activity = utc_now_iso()
            return True
        except asyncio.QueueFull:
            print(f"[SSE] Worker {worker_id} queue full, dropping event")
            return False
    
    # ==================== Event Helpers ====================
    
    async def broadcast_new_message(
        self,
        message_id: str,
        agent_id: str,
        message_type: str,
    ) -> int:
        """Broadcast new message event."""
        return await self.broadcast(
            SSEEvent.NEW_MESSAGE,
            {
                "id": message_id,
                "agent_id": agent_id,
                "type": message_type,
            }
        )
    
    async def broadcast_new_task(
        self,
        task_id: str,
        agent_id: str,
        task_type: str,
        action: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> int:
        """Broadcast new task event."""
        return await self.broadcast(
            SSEEvent.NEW_TASK,
            {
                "id": task_id,
                "agent_id": agent_id,
                "type": task_type,
                "action": action,
                "idempotency_key": idempotency_key,
            }
        )
    
    async def broadcast_task_result(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> int:
        """Broadcast task result event."""
        return await self.broadcast(
            SSEEvent.TASK_RESULT,
            {
                "id": task_id,
                "status": status,
                "result": result,
                "error": error,
            }
        )
    
    async def broadcast_round_complete(
        self,
        subagent_id: str,
        round_id: str,
    ) -> int:
        """Broadcast round complete event."""
        return await self.broadcast(
            SSEEvent.ROUND_COMPLETE,
            {
                "subagent_id": subagent_id,
                "round_id": round_id,
            }
        )
    
    # ==================== Heartbeat ====================
    
    async def start_heartbeat(self) -> None:
        """Start the heartbeat background task."""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            print(f"[SSE] Heartbeat started (interval: {self._heartbeat_interval}s)")
    
    async def stop_heartbeat(self) -> None:
        """Stop the heartbeat background task."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            print("[SSE] Heartbeat stopped")
    
    async def _heartbeat_loop(self) -> None:
        """Background task that sends periodic heartbeats."""
        while not self._shutdown:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                await self.broadcast(
                    SSEEvent.HEARTBEAT,
                    {"time": utc_now_iso()}
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[SSE] Heartbeat error: {e}")
    
    # ==================== Shutdown ====================
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the broadcaster."""
        self._shutdown = True
        
        # Stop heartbeat
        await self.stop_heartbeat()
        
        # Send shutdown signal to all Workers
        await self.broadcast(
            SSEEvent.WORKER_SHUTDOWN,
            {"reason": "gateway_shutdown"}
        )
        
        # Clear connections
        self._connections.clear()
        print("[SSE] Broadcaster shutdown complete")
    
    # ==================== SSE Generator ====================
    
    async def event_generator(
        self,
        worker_id: str,
        queue: asyncio.Queue,
    ) -> AsyncGenerator[str, None]:
        """
        Generate SSE formatted events for a Worker.
        
        Args:
            worker_id: Worker identifier
            queue: Event queue for this worker
        
        Yields:
            SSE formatted event strings
        """
        try:
            while not self._shutdown:
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(
                        queue.get(),
                        timeout=self._heartbeat_interval + 5
                    )
                    
                    # Format as SSE
                    event_type = event.get("event", "message")
                    data = json.dumps(event.get("data", {}))
                    
                    yield f"event: {event_type}\n"
                    yield f"data: {data}\n\n"
                    
                except asyncio.TimeoutError:
                    # Send keepalive comment
                    yield f": keepalive {utc_now_iso()}\n\n"
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[SSE] Event generator error for {worker_id}: {e}")
        finally:
            self.unregister(worker_id)


# ==================== Singleton Instance ====================

_broadcaster: Optional[WorkerBroadcaster] = None


def get_worker_broadcaster() -> WorkerBroadcaster:
    """Get the global WorkerBroadcaster instance."""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = WorkerBroadcaster()
    return _broadcaster


async def init_worker_broadcaster() -> WorkerBroadcaster:
    """Initialize and start the global broadcaster."""
    broadcaster = get_worker_broadcaster()
    await broadcaster.start_heartbeat()
    return broadcaster


async def shutdown_worker_broadcaster() -> None:
    """Shutdown the global broadcaster."""
    global _broadcaster
    if _broadcaster:
        await _broadcaster.shutdown()
        _broadcaster = None
