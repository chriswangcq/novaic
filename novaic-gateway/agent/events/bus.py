"""
EventBus - Central event queue and dispatch system

The EventBus is the heart of the event-driven architecture.
It receives events from various sources and dispatches them to handlers.
"""

import asyncio
import logging
from typing import Callable, Dict, List, Optional, Awaitable
from collections import defaultdict
from datetime import datetime

from .models import AgentEvent, EventType, EventResult

logger = logging.getLogger(__name__)


class EventBus:
    """
    Central event bus for the agent system.
    
    Features:
    - Priority queue: Events are processed by priority, then by timestamp
    - Type-based routing: Handlers can subscribe to specific event types
    - Async processing: All event handling is asynchronous
    - Error isolation: Handler errors don't crash the bus
    """
    
    def __init__(self, max_queue_size: int = 1000):
        """
        Initialize the EventBus.
        
        Args:
            max_queue_size: Maximum number of events in queue
        """
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._subscribers: Dict[EventType, List[Callable[[AgentEvent], Awaitable[EventResult]]]] = defaultdict(list)
        self._global_subscribers: List[Callable[[AgentEvent], Awaitable[EventResult]]] = []
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "started_at": None,
        }
    
    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[AgentEvent], Awaitable[EventResult]]
    ) -> None:
        """
        Subscribe a handler to a specific event type.
        
        Args:
            event_type: The type of events to handle
            handler: Async function that takes an AgentEvent and returns EventResult
        """
        self._subscribers[event_type].append(handler)
        logger.debug(f"[EventBus] Subscribed handler to {event_type.value}")
    
    def subscribe_all(
        self,
        handler: Callable[[AgentEvent], Awaitable[EventResult]]
    ) -> None:
        """
        Subscribe a handler to all event types.
        
        Args:
            handler: Async function that handles all events
        """
        self._global_subscribers.append(handler)
        logger.debug("[EventBus] Subscribed global handler")
    
    def unsubscribe(
        self,
        event_type: EventType,
        handler: Callable[[AgentEvent], Awaitable[EventResult]]
    ) -> bool:
        """
        Unsubscribe a handler from an event type.
        
        Returns:
            True if handler was found and removed
        """
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            return True
        return False
    
    async def publish(self, event: AgentEvent) -> str:
        """
        Publish an event to the bus.
        
        Args:
            event: The event to publish
        
        Returns:
            The event ID
        
        Raises:
            asyncio.QueueFull: If queue is at max capacity
        """
        await self._queue.put(event)
        self._stats["events_published"] += 1
        logger.debug(f"[EventBus] Published event: {event.id} ({event.type.value})")
        return event.id
    
    def publish_nowait(self, event: AgentEvent) -> str:
        """
        Publish an event without waiting (non-blocking).
        
        Raises:
            asyncio.QueueFull: If queue is full
        """
        self._queue.put_nowait(event)
        self._stats["events_published"] += 1
        return event.id
    
    async def start(self) -> None:
        """Start the event processing loop."""
        if self._running:
            logger.warning("[EventBus] Already running")
            return
        
        self._running = True
        self._stats["started_at"] = datetime.now().isoformat()
        self._task = asyncio.create_task(self._process_loop())
        logger.info("[EventBus] Started")
    
    async def stop(self, timeout: float = 5.0) -> None:
        """
        Stop the event processing loop.
        
        Args:
            timeout: Maximum time to wait for current event to finish
        """
        if not self._running:
            return
        
        self._running = False
        
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=timeout)
            except asyncio.TimeoutError:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
        
        logger.info("[EventBus] Stopped")
    
    async def _process_loop(self) -> None:
        """Main event processing loop."""
        while self._running:
            try:
                # Wait for an event with timeout to allow checking _running flag
                try:
                    event = await asyncio.wait_for(self._queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                
                # Dispatch the event
                await self._dispatch(event)
                self._stats["events_processed"] += 1
                
            except Exception as e:
                logger.error(f"[EventBus] Error in process loop: {e}")
                self._stats["events_failed"] += 1
    
    async def _dispatch(self, event: AgentEvent) -> List[EventResult]:
        """
        Dispatch an event to all subscribed handlers.
        
        Args:
            event: The event to dispatch
        
        Returns:
            List of results from all handlers
        """
        results = []
        handlers = []
        
        # Collect handlers for this event type
        handlers.extend(self._subscribers.get(event.type, []))
        handlers.extend(self._global_subscribers)
        
        if not handlers:
            logger.warning(f"[EventBus] No handlers for event type: {event.type.value}")
            return results
        
        # Call all handlers
        start_time = datetime.now()
        
        for handler in handlers:
            try:
                result = await handler(event)
                results.append(result)
            except Exception as e:
                logger.error(f"[EventBus] Handler error for {event.id}: {e}")
                results.append(EventResult(
                    event_id=event.id,
                    success=False,
                    error=str(e)
                ))
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        logger.debug(f"[EventBus] Dispatched {event.id} to {len(handlers)} handlers in {duration_ms}ms")
        
        return results
    
    @property
    def queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()
    
    @property
    def is_running(self) -> bool:
        """Check if the bus is running."""
        return self._running
    
    def get_stats(self) -> Dict:
        """Get bus statistics."""
        return {
            **self._stats,
            "queue_size": self.queue_size,
            "is_running": self._running,
            "subscriber_counts": {
                event_type.value: len(handlers)
                for event_type, handlers in self._subscribers.items()
            },
            "global_subscribers": len(self._global_subscribers),
        }
