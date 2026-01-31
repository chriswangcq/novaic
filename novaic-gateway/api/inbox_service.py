"""
Inbox Service

Service layer for Inbox operations.
Handles message ingestion, retrieval, and coordination with EventBus.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from db.database import get_database
from db.repositories.inbox import InboxRepository
from db.repositories.chat import ChatRepository


class InboxService:
    """
    Service for managing Inbox operations.
    
    Responsibilities:
    - Add messages to Inbox
    - Coordinate with ChatRepository for chat history
    - Notify EventBus of new messages
    """
    
    def __init__(self, agent_id: Optional[str] = None):
        self._inbox_repo: Optional[InboxRepository] = None
        self._chat_repo: Optional[ChatRepository] = None
        self._agent_id = agent_id
        self._event_bus = None
        self._sse_broadcast_callback = None
    
    @property
    def inbox_repo(self) -> InboxRepository:
        if self._inbox_repo is None:
            self._inbox_repo = InboxRepository(get_database())
        return self._inbox_repo
    
    @property
    def chat_repo(self) -> ChatRepository:
        if self._chat_repo is None:
            self._chat_repo = ChatRepository(get_database())
        return self._chat_repo
    
    @property
    def agent_id(self) -> Optional[str]:
        """Get current agent ID.
        
        Returns:
            The current agent ID, or None if not set.
        """
        if self._agent_id:
            return self._agent_id
        # Try to get from config
        try:
            from config.agents import get_agent_config_manager
            mgr = get_agent_config_manager()
            current = mgr.get_current_agent()
            if current:
                return current.id
        except Exception as e:
            logger.warning(f"[InboxService] Failed to get current agent ID: {e}")
        return None
    
    def set_agent_id(self, agent_id: str):
        """Set the current agent ID."""
        self._agent_id = agent_id
    
    def _require_agent_id(self, agent_id: Optional[str] = None) -> str:
        """Get agent ID, raising error if not available."""
        aid = agent_id or self.agent_id
        if not aid:
            raise ValueError("No agent ID available. Please select an agent first.")
        return aid
    
    def set_event_bus(self, event_bus):
        """Set EventBus for notifications."""
        self._event_bus = event_bus
    
    def set_sse_broadcast(self, callback):
        """Set SSE broadcast callback."""
        self._sse_broadcast_callback = callback
    
    async def add_message(
        self,
        msg_type: str,
        content: str,
        priority: str = "normal",
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a message to the Inbox.
        
        This is the main entry point for all input messages.
        
        Args:
            msg_type: Message type (USER_MESSAGE, SYSTEM_MESSAGE, WEBHOOK, etc.)
            content: Message content
            priority: Priority level (critical, high, normal, low)
            source: Message source (user, system:bootstrap, webhook:xxx, etc.)
            metadata: Additional metadata
            agent_id: Target agent ID (defaults to current agent)
        
        Returns:
            The created message dict
        """
        aid = self._require_agent_id(agent_id)
        
        # Map priority string to int
        priority_map = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        priority_int = priority_map.get(priority.lower(), 2)
        
        # 1. Add to inbox_messages
        msg = await self.inbox_repo.add_message(
            agent_id=aid,
            msg_type=msg_type,
            content=content,
            priority=priority_int,
            source=source,
            metadata=metadata,
        )
        
        # 2. Add to chat_messages (for chat history display)
        await self.chat_repo.add_message(
            agent_id=aid,
            id=msg["id"],
            type=msg_type,
            content=content,
            metadata={
                "source": source,
                "priority": priority,
                "inbox_id": msg["id"],
                **(metadata or {}),
            },
        )
        
        # 3. Broadcast SSE
        if self._sse_broadcast_callback:
            await self._sse_broadcast_callback({
                "id": msg["id"],
                "type": msg_type,
                "content": content,
                "source": source,
                "priority": priority,
                "timestamp": msg["created_at"],
            })
        
        # 4. Notify EventBus
        if self._event_bus:
            self._event_bus.notify_new_message(aid)
        
        return msg
    
    async def pop_message(self, agent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get and claim the next pending message.
        
        Args:
            agent_id: Agent ID (defaults to current agent)
        
        Returns:
            Message dict or None if no pending messages
        """
        aid = self._require_agent_id(agent_id)
        return await self.inbox_repo.pop_message(aid)
    
    async def mark_done(self, msg_id: str):
        """Mark a message as done."""
        await self.inbox_repo.mark_done(msg_id)
    
    async def mark_failed(self, msg_id: str, error: Optional[str] = None):
        """Mark a message as failed."""
        await self.inbox_repo.mark_failed(msg_id, error)
    
    async def get_inbox_summary(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Inbox summary.
        
        Args:
            agent_id: Agent ID (defaults to current agent)
        
        Returns:
            Summary dict with pending_count and messages list
        """
        aid = self._require_agent_id(agent_id)
        
        pending_count = await self.inbox_repo.get_pending_count(aid)
        messages = await self.inbox_repo.get_pending_messages(aid, limit=5)
        
        # Map priority int to string
        priority_names = {0: "critical", 1: "high", 2: "normal", 3: "low"}
        
        return {
            "pending_count": pending_count,
            "messages": [
                {
                    "id": m["id"],
                    "type": m["type"],
                    "summary": m["content"][:50] + "..." if len(m["content"] or "") > 50 else m["content"],
                    "priority": priority_names.get(m["priority"], "normal"),
                    "source": m["source"],
                    "created_at": m["created_at"],
                }
                for m in messages
            ],
        }
    
    async def get_pending_count(self, agent_id: Optional[str] = None) -> int:
        """Get count of pending messages."""
        aid = self._require_agent_id(agent_id)
        return await self.inbox_repo.get_pending_count(aid)
    
    async def recover_processing(self, agent_id: Optional[str] = None) -> int:
        """
        Recover messages stuck in processing state.
        
        Call this on service startup.
        
        Args:
            agent_id: Agent ID (defaults to current agent)
        
        Returns:
            Number of messages recovered
        """
        aid = self._require_agent_id(agent_id)
        return await self.inbox_repo.recover_processing(aid)
    
    async def cleanup_old_messages(
        self,
        agent_id: Optional[str] = None,
        days: int = 7,
    ) -> int:
        """
        Cleanup old completed/failed messages.
        
        Args:
            agent_id: Agent ID (defaults to current agent)
            days: Delete messages older than this many days
        
        Returns:
            Number of messages deleted
        """
        aid = self._require_agent_id(agent_id)
        return await self.inbox_repo.delete_old_messages(aid, days)


# Global instance
_inbox_service: Optional[InboxService] = None


def get_inbox_service() -> InboxService:
    """Get the global InboxService instance."""
    global _inbox_service
    if _inbox_service is None:
        _inbox_service = InboxService()
    return _inbox_service


def set_inbox_service_agent(agent_id: str):
    """Set the agent ID for the global InboxService."""
    get_inbox_service().set_agent_id(agent_id)
