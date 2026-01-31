"""
Agent Runner

The consumer that processes messages from the Inbox.
Runs in a loop when Agent is AWAKE, taking messages and processing them.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from api.inbox_service import InboxService
    from db.repositories.agent_state import AgentStateRepository
    from agent.events.bus import EventBus
    from core.agent import NovAICAgent

logger = logging.getLogger(__name__)


class AgentRunner:
    """
    Agent consumer that processes messages from the Inbox.
    
    Responsibilities:
    - Run processing loop when Agent is AWAKE
    - Pop messages from Inbox
    - Call Agent to process each message
    - Handle errors and update message status
    - Stop when Agent enters SLEEP state
    """
    
    def __init__(
        self,
        agent_id: str,
        agent: "NovAICAgent",
        inbox_service: "InboxService",
        state_repo: "AgentStateRepository",
        event_bus: "EventBus",
    ):
        """
        Initialize the AgentRunner.
        
        Args:
            agent_id: Agent ID
            agent: NovAICAgent instance
            inbox_service: InboxService for message access
            state_repo: AgentStateRepository for state access
            event_bus: EventBus for notifications
        """
        self.agent_id = agent_id
        self.agent = agent
        self.inbox_service = inbox_service
        self.state_repo = state_repo
        self.event_bus = event_bus
        
        # Callbacks
        self._broadcast_log_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
        self._broadcast_chat_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
        
        # State
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._new_message_event = asyncio.Event()
        
        # Current processing info
        self._current_message_id: Optional[str] = None
    
    def set_broadcast_callbacks(
        self,
        log_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        chat_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ):
        """Set callbacks for broadcasting logs and chat messages."""
        self._broadcast_log_callback = log_callback
        self._broadcast_chat_callback = chat_callback
    
    def notify_new_message(self):
        """Notify that a new message is available."""
        self._new_message_event.set()
    
    async def start(self):
        """Start the processing loop."""
        if self._running:
            logger.debug(f"[AgentRunner] Already running for agent {self.agent_id}")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"[AgentRunner] Started for agent {self.agent_id}")
    
    async def stop(self):
        """Stop the processing loop."""
        self._running = False
        self._new_message_event.set()  # Wake up the loop
        
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning(f"[AgentRunner] Timeout waiting for task to finish, cancelling")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
        
        logger.info(f"[AgentRunner] Stopped for agent {self.agent_id}")
    
    @property
    def is_running(self) -> bool:
        """Check if runner is currently running."""
        return self._running
    
    @property
    def current_message_id(self) -> Optional[str]:
        """Get the ID of the message currently being processed."""
        return self._current_message_id
    
    async def _run_loop(self):
        """Main processing loop."""
        logger.debug(f"[AgentRunner] Entering run loop for agent {self.agent_id}")
        
        while self._running:
            # Check Agent state
            state_data = await self.state_repo.get_state(self.agent_id)
            if state_data["state"] != "awake":
                logger.info(f"[AgentRunner] Agent {self.agent_id} is not awake, stopping runner")
                break
            
            # Try to get a message from Inbox
            msg = await self.inbox_service.pop_message(self.agent_id)
            
            if msg:
                # Process the message
                await self._process_message(msg)
                
                # Update last active time
                await self.state_repo.update_last_active(self.agent_id)
            else:
                # No messages, wait for notification
                try:
                    await asyncio.wait_for(
                        self._new_message_event.wait(),
                        timeout=5.0
                    )
                    self._new_message_event.clear()
                except asyncio.TimeoutError:
                    # Timeout, loop again to check state
                    pass
        
        self._running = False
        logger.debug(f"[AgentRunner] Exited run loop for agent {self.agent_id}")
    
    async def _process_message(self, msg: Dict[str, Any]):
        """
        Process a single message.
        
        Args:
            msg: Message dict from Inbox
        """
        msg_id = msg["id"]
        msg_type = msg["type"]
        content = msg["content"] or ""
        metadata = msg.get("metadata", {})
        
        self._current_message_id = msg_id
        
        logger.info(f"[AgentRunner] Processing message {msg_id}: type={msg_type}")
        
        try:
            # Resolve model configuration
            model = metadata.get("model")
            api_key_id = metadata.get("api_key_id")
            provider = None
            api_base = None
            api_key = None
            
            # Get API key configuration if specified
            if api_key_id:
                try:
                    from config import get_config_manager
                    config = get_config_manager().load()
                    for key in config.api_keys or []:
                        if key.id == api_key_id:
                            provider = key.provider.value if hasattr(key.provider, 'value') else key.provider
                            api_base = key.api_base
                            api_key = key.api_key
                            break
                except Exception as e:
                    logger.warning(f"[AgentRunner] Could not load API key config: {e}")
            
            # Initialize agent if needed
            if not self.agent._tools_initialized:
                await self.agent.initialize()
            
            # Process with agent
            chat_reply_called = False
            final_content = None
            
            async for event in self.agent.chat(
                user_message=content,
                model=model,
                provider=provider,
                api_base=api_base,
                api_key=api_key,
            ):
                event_type = event.get("type", "unknown")
                event_data = event.get("data", {})
                
                # Broadcast execution log
                if self._broadcast_log_callback:
                    log_entry = {
                        "type": event_type,
                        "timestamp": datetime.now().isoformat(),
                        "data": event_data,
                        "message_id": msg_id,
                    }
                    await self._broadcast_log_callback(log_entry)
                
                # Track if chat_reply was called
                if event_type == "tool_end":
                    tool_name = event_data.get("tool", "") if isinstance(event_data, dict) else ""
                    if tool_name == "chat_reply":
                        chat_reply_called = True
                
                # Capture final response for fallback
                if event_type == "final":
                    if isinstance(event_data, str):
                        final_content = event_data
                    elif isinstance(event_data, dict):
                        final_content = event_data.get("content") or event_data.get("data") or str(event_data)
                    else:
                        final_content = str(event_data)
            
            # Fallback: If agent didn't use chat_reply, send final_content as reply
            if not chat_reply_called and final_content and self._broadcast_chat_callback:
                from uuid import uuid4
                agent_reply = {
                    "id": str(uuid4())[:12],
                    "type": "AGENT_REPLY",
                    "timestamp": datetime.now().isoformat(),
                    "message": final_content,
                }
                await self._broadcast_chat_callback(agent_reply)
            
            # Mark message as done
            await self.inbox_service.mark_done(msg_id)
            logger.info(f"[AgentRunner] Message {msg_id} processed successfully")
            
        except Exception as e:
            logger.error(f"[AgentRunner] Error processing message {msg_id}: {e}")
            
            # Mark message as failed
            await self.inbox_service.mark_failed(msg_id, str(e))
            
            # Broadcast error log
            if self._broadcast_log_callback:
                await self._broadcast_log_callback({
                    "type": "error",
                    "timestamp": datetime.now().isoformat(),
                    "data": {"error": str(e)},
                    "message_id": msg_id,
                })
        
        finally:
            self._current_message_id = None
    
    async def process_single_message(self, msg: Dict[str, Any]):
        """
        Process a single message without starting the loop.
        
        Useful for testing or one-off processing.
        
        Args:
            msg: Message dict
        """
        await self._process_message(msg)
