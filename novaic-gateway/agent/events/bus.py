"""
EventBus - Lightweight notification system for Inbox

The EventBus is a simple notification mechanism for the Inbox system.
It notifies InboxMonitor when new messages arrive.

Note: This is a simplified version. Messages are persisted in the database,
EventBus only handles in-memory notifications.
"""

import asyncio
import logging
from typing import Callable, Dict, List, Optional, Awaitable, Any
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class EventBus:
    """
    Lightweight EventBus for Inbox notifications.
    
    This is a simplified version that only handles:
    - New message notifications (per agent)
    - Generic event subscriptions (for backward compatibility)
    
    All message persistence is handled by InboxService/InboxRepository.
    EventBus only triggers in-memory notifications.
    """
    
    def __init__(self):
        """Initialize the EventBus."""
        # Per-agent new message events
        self._new_message_events: Dict[str, asyncio.Event] = {}
        
        # Generic event subscribers (for backward compatibility)
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = defaultdict(list)
        
        # Statistics
        self._stats = {
            "notifications_sent": 0,
            "started_at": datetime.now().isoformat(),
        }
        
        logger.info("[EventBus] Initialized (lightweight mode)")
    
    def get_new_message_event(self, agent_id: str) -> asyncio.Event:
        """
        Get the new message event for an agent.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            asyncio.Event that is set when new messages arrive
        """
        if agent_id not in self._new_message_events:
            self._new_message_events[agent_id] = asyncio.Event()
        return self._new_message_events[agent_id]
    
    def notify_new_message(self, agent_id: str):
        """
        Notify that a new message has arrived for an agent.
        
        This triggers the InboxMonitor to check the Inbox.
        
        Args:
            agent_id: Agent ID
        """
        event = self.get_new_message_event(agent_id)
        event.set()
        self._stats["notifications_sent"] += 1
        logger.debug(f"[EventBus] New message notification for agent {agent_id}")
    
    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: Event type string
            handler: Async handler function
        """
        self._subscribers[event_type].append(handler)
        logger.debug(f"[EventBus] Subscribed handler to {event_type}")
    
    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Dict[str, Any]], Awaitable[None]]
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
    
    async def emit(self, event_type: str, data: Dict[str, Any]):
        """
        Emit an event to all subscribers.
        
        Args:
            event_type: Event type string
            data: Event data
        """
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"[EventBus] Handler error for {event_type}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get EventBus statistics."""
        return {
            **self._stats,
            "active_agents": len(self._new_message_events),
            "subscriber_counts": {
                event_type: len(handlers)
                for event_type, handlers in self._subscribers.items()
            },
        }
    
    async def start(self) -> None:
        """Start the EventBus (no-op for lightweight version)."""
        logger.info("[EventBus] Started (lightweight mode - no background processing)")
    
    async def stop(self) -> None:
        """Stop the EventBus (clears all events)."""
        for event in self._new_message_events.values():
            event.set()  # Wake up any waiting coroutines
        self._new_message_events.clear()
        logger.info("[EventBus] Stopped")
