"""
Inbox Monitor

Monitors the Inbox for new messages and decides whether to wake the Agent.
This is the bridge between message ingestion and Agent processing.
"""

import asyncio
import logging
import re
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from agent.events.bus import EventBus
    from agent.runner import AgentRunner
    from api.inbox_service import InboxService
    from db.repositories.agent_state import AgentStateRepository

logger = logging.getLogger(__name__)


class InboxMonitor:
    """
    Monitors Inbox for new messages and coordinates Agent wake-up.
    
    Responsibilities:
    - Listen for new message notifications from EventBus
    - Check Agent state from database
    - Decide whether to wake the Agent based on wake triggers
    - Notify AgentRunner when Agent should process messages
    """
    
    def __init__(
        self,
        agent_id: str,
        inbox_service: "InboxService",
        state_repo: "AgentStateRepository",
        event_bus: "EventBus",
    ):
        """
        Initialize the InboxMonitor.
        
        Args:
            agent_id: Agent ID to monitor
            inbox_service: InboxService for message access
            state_repo: AgentStateRepository for state access
            event_bus: EventBus for notifications
        """
        self.agent_id = agent_id
        self.inbox_service = inbox_service
        self.state_repo = state_repo
        self.event_bus = event_bus
        
        # AgentRunner will be set later
        self._agent_runner: Optional["AgentRunner"] = None
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def set_agent_runner(self, runner: "AgentRunner"):
        """Set the AgentRunner to notify when messages need processing."""
        self._agent_runner = runner
    
    async def start(self):
        """Start the monitor."""
        if self._running:
            logger.warning(f"[InboxMonitor] Already running for agent {self.agent_id}")
            return
        
        self._running = True
        
        # Check for pending messages on startup
        await self._check_and_process()
        
        # Start monitoring loop
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"[InboxMonitor] Started for agent {self.agent_id}")
    
    async def stop(self):
        """Stop the monitor."""
        self._running = False
        
        # Wake up the monitor loop so it can exit
        self.event_bus.notify_new_message(self.agent_id)
        
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
        
        logger.info(f"[InboxMonitor] Stopped for agent {self.agent_id}")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        new_message_event = self.event_bus.get_new_message_event(self.agent_id)
        
        while self._running:
            # Wait for new message notification
            await new_message_event.wait()
            new_message_event.clear()
            
            if not self._running:
                break
            
            await self._check_and_process()
    
    async def _check_and_process(self):
        """Check Inbox and decide whether to wake Agent."""
        try:
            # Get pending message count
            pending_count = await self.inbox_service.get_pending_count(self.agent_id)
            
            if pending_count == 0:
                return
            
            # Get Agent state from database
            state_data = await self.state_repo.get_state(self.agent_id)
            state = state_data["state"]
            
            logger.debug(f"[InboxMonitor] Agent {self.agent_id}: state={state}, pending={pending_count}")
            
            if state == "sleep":
                # Agent is sleeping, check if we should wake it
                should_wake = await self._should_wake(state_data)
                
                if should_wake:
                    logger.info(f"[InboxMonitor] Waking agent {self.agent_id}")
                    await self._wake_agent()
                else:
                    logger.debug(f"[InboxMonitor] Agent {self.agent_id} sleeping, wake conditions not met")
            
            elif state == "awake":
                # Agent is awake, notify runner of new messages
                if self._agent_runner:
                    self._agent_runner.notify_new_message()
        
        except Exception as e:
            logger.error(f"[InboxMonitor] Error checking inbox: {e}")
    
    async def _should_wake(self, state_data: Dict[str, Any]) -> bool:
        """
        Check if Agent should be woken up.
        
        Args:
            state_data: Agent state from database
        
        Returns:
            True if Agent should be woken
        """
        wake_triggers = state_data.get("wake_triggers", [])
        
        # If no wake triggers defined, wake on any message
        if not wake_triggers:
            return True
        
        # Get pending messages to check against triggers
        messages = await self.inbox_service.inbox_repo.get_pending_messages(
            self.agent_id, limit=5
        )
        
        if not messages:
            return False
        
        for msg in messages:
            msg_type = msg.get("type", "")
            content = msg.get("content", "")
            priority = msg.get("priority", 2)
            
            for trigger in wake_triggers:
                trigger_type = trigger.get("type")
                
                # Wake on any user message
                if trigger_type == "user_response":
                    if msg_type == "USER_MESSAGE":
                        logger.debug(f"[InboxMonitor] Wake trigger matched: user_response")
                        return True
                
                # Wake on keyword match
                elif trigger_type == "keyword":
                    pattern = trigger.get("pattern", "")
                    if pattern and re.search(pattern, content, re.IGNORECASE):
                        logger.debug(f"[InboxMonitor] Wake trigger matched: keyword '{pattern}'")
                        return True
                
                # Wake on high priority messages
                elif trigger_type == "high_priority":
                    if priority <= 1:  # CRITICAL (0) or HIGH (1)
                        logger.debug(f"[InboxMonitor] Wake trigger matched: high_priority")
                        return True
                
                # Wake on specific message type
                elif trigger_type == "message_type":
                    target_type = trigger.get("message_type", "")
                    if msg_type == target_type:
                        logger.debug(f"[InboxMonitor] Wake trigger matched: message_type '{target_type}'")
                        return True
                
                # Wake on system message
                elif trigger_type == "system_message":
                    if msg_type == "SYSTEM_MESSAGE":
                        logger.debug(f"[InboxMonitor] Wake trigger matched: system_message")
                        return True
        
        return False
    
    async def _wake_agent(self):
        """Wake up the Agent."""
        # Update state in database
        await self.state_repo.set_awake(self.agent_id)
        
        # Start AgentRunner if available
        if self._agent_runner:
            await self._agent_runner.start()
        
        # Emit wake event for logging/UI
        await self.event_bus.emit("agent_wake", {
            "agent_id": self.agent_id,
            "reason": "inbox_message",
        })
    
    async def force_wake(self, reason: str = "manual"):
        """
        Force wake the Agent regardless of triggers.
        
        Args:
            reason: Reason for waking
        """
        state_data = await self.state_repo.get_state(self.agent_id)
        
        if state_data["state"] == "sleep":
            logger.info(f"[InboxMonitor] Force waking agent {self.agent_id}: {reason}")
            await self.state_repo.set_awake(self.agent_id)
            
            if self._agent_runner:
                await self._agent_runner.start()
            
            await self.event_bus.emit("agent_wake", {
                "agent_id": self.agent_id,
                "reason": reason,
            })
