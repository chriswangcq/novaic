"""
AgentEventHandler - Bridges EventBus and Agent

This handler receives events from the EventBus and routes them to the Agent.
It also manages agent state transitions and response routing.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

from .models import AgentEvent, EventType, EventResult, EventPriority
from .bus import EventBus
from ..core.state import AgentState, StateManager

logger = logging.getLogger(__name__)


class AgentEventHandler:
    """
    Handles events from the EventBus and routes them to the Agent.
    
    Responsibilities:
    - Check agent state before processing
    - Queue events if agent is busy
    - Route responses to appropriate channels
    - Track event processing metrics
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        state_manager: StateManager,
        agent_callback: Callable[[str, str], Awaitable[str]],  # (message, session_id) -> response
    ):
        """
        Initialize the handler.
        
        Args:
            event_bus: The EventBus to subscribe to
            state_manager: Agent state manager
            agent_callback: Async function to call the agent
        """
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_callback = agent_callback
        
        # Response callbacks (reply_channel -> callback)
        self._response_callbacks: Dict[str, Callable[[str, Dict], Awaitable[None]]] = {}
        
        # Event processing queue for when agent is busy
        self._pending_events: asyncio.Queue = asyncio.Queue()
        
        # Statistics
        self._stats = {
            "events_handled": 0,
            "events_queued": 0,
            "events_skipped": 0,
        }
        
        # Subscribe to relevant event types
        self._setup_subscriptions()
    
    def _setup_subscriptions(self) -> None:
        """Set up event subscriptions."""
        # Subscribe to all events that need agent processing
        for event_type in [
            EventType.USER_MESSAGE,
            EventType.CRON_TRIGGER,
            EventType.WEBHOOK,
            EventType.SUBAGENT_RESULT,
            EventType.WAKE_REQUEST,
        ]:
            self.event_bus.subscribe(event_type, self._handle_event)
    
    def register_response_callback(
        self,
        channel: str,
        callback: Callable[[str, Dict], Awaitable[None]]
    ) -> None:
        """
        Register a callback for routing responses.
        
        Args:
            channel: Channel identifier (e.g., "http", "websocket", "wechat")
            callback: Async function(event_id, response_data) to send response
        """
        self._response_callbacks[channel] = callback
        logger.debug(f"[EventHandler] Registered response callback for channel: {channel}")
    
    async def _handle_event(self, event: AgentEvent) -> EventResult:
        """
        Handle an incoming event.
        
        This is the main event handler that:
        1. Checks agent state
        2. Processes or queues the event
        3. Routes the response
        """
        start_time = datetime.now()
        
        try:
            # Check if this is a wake request
            if event.type == EventType.WAKE_REQUEST:
                return await self._handle_wake_request(event)
            
            # Check agent state
            current_state = self.state_manager.get_state()
            
            if current_state == AgentState.SLEEP:
                # Agent is sleeping, skip unless it's a high priority event
                if event.priority.value > EventPriority.HIGH.value:
                    logger.debug(f"[EventHandler] Skipping event {event.id} - agent is sleeping")
                    self._stats["events_skipped"] += 1
                    return EventResult(
                        event_id=event.id,
                        success=False,
                        error="Agent is sleeping"
                    )
                else:
                    # Wake up the agent for high priority events
                    self.state_manager.set_state(AgentState.AWAKE)
            
            elif current_state == AgentState.BUSY:
                # Agent is busy, queue the event
                await self._pending_events.put(event)
                self._stats["events_queued"] += 1
                logger.debug(f"[EventHandler] Queued event {event.id} - agent is busy")
                return EventResult(
                    event_id=event.id,
                    success=True,
                    response={"status": "queued"}
                )
            
            # Process the event
            result = await self._process_event(event)
            
            # Calculate duration
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            result.duration_ms = duration_ms
            
            self._stats["events_handled"] += 1
            
            # Route response if needed
            if event.reply_channel and result.response:
                await self._route_response(event, result)
            
            # Process any pending events
            asyncio.create_task(self._process_pending_events())
            
            return result
            
        except Exception as e:
            logger.error(f"[EventHandler] Error handling event {event.id}: {e}")
            return EventResult(
                event_id=event.id,
                success=False,
                error=str(e),
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
    
    async def _process_event(self, event: AgentEvent) -> EventResult:
        """
        Process a single event by calling the agent.
        
        Args:
            event: The event to process
        
        Returns:
            EventResult with the agent's response
        """
        # Set agent to busy
        self.state_manager.set_state(AgentState.BUSY)
        
        try:
            # Extract message from event
            message = self._extract_message(event)
            session_id = event.session_id or "main"
            
            # Call the agent
            response = await self.agent_callback(message, session_id)
            
            return EventResult(
                event_id=event.id,
                success=True,
                response={"content": response}
            )
            
        finally:
            # Return to awake state
            self.state_manager.set_state(AgentState.AWAKE)
    
    def _extract_message(self, event: AgentEvent) -> str:
        """Extract the message content from an event."""
        payload = event.payload
        
        if event.type == EventType.USER_MESSAGE:
            return payload.get("content", "")
        
        elif event.type == EventType.CRON_TRIGGER:
            return payload.get("message", f"Cron trigger: {payload.get('trigger_name', 'unknown')}")
        
        elif event.type == EventType.WEBHOOK:
            webhook_name = payload.get("webhook_name", "unknown")
            data = payload.get("data", {})
            return f"Webhook '{webhook_name}' triggered with data: {data}"
        
        elif event.type == EventType.SUBAGENT_RESULT:
            subagent_id = payload.get("subagent_id", "unknown")
            result = payload.get("result", {})
            return f"Sub-agent {subagent_id} completed: {result}"
        
        else:
            return str(payload)
    
    async def _route_response(self, event: AgentEvent, result: EventResult) -> None:
        """Route response to the appropriate channel."""
        channel = event.reply_channel
        
        if channel not in self._response_callbacks:
            logger.warning(f"[EventHandler] No callback for channel: {channel}")
            return
        
        try:
            callback = self._response_callbacks[channel]
            await callback(event.id, result.response or {})
        except Exception as e:
            logger.error(f"[EventHandler] Error routing response: {e}")
    
    async def _handle_wake_request(self, event: AgentEvent) -> EventResult:
        """Handle a wake request event."""
        current_state = self.state_manager.get_state()
        
        if current_state == AgentState.SLEEP:
            self.state_manager.set_state(AgentState.AWAKE)
            logger.info(f"[EventHandler] Agent woken by: {event.source}")
            return EventResult(
                event_id=event.id,
                success=True,
                response={"status": "awake", "previous_state": "sleep"}
            )
        else:
            return EventResult(
                event_id=event.id,
                success=True,
                response={"status": current_state.value, "message": "Already awake"}
            )
    
    async def _process_pending_events(self) -> None:
        """Process any queued events."""
        while not self._pending_events.empty():
            # Check if agent is available
            if self.state_manager.get_state() == AgentState.BUSY:
                break
            
            try:
                event = self._pending_events.get_nowait()
                await self._handle_event(event)
            except asyncio.QueueEmpty:
                break
    
    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            **self._stats,
            "pending_events": self._pending_events.qsize(),
            "registered_channels": list(self._response_callbacks.keys()),
        }
