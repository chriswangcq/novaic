"""
Chat Service - Database-backed Chat State Management

Handles all chat-related operations using SQLite for state management.
Simplified in v3: unified chat_messages table with read field.
All operations are isolated per agent_id.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4

from db.database import get_database
from db.repositories.chat import ChatRepository


class ChatService:
    """
    Service for managing chat state using database.
    
    All chat messages, questions, responses, and agent state
    are stored in SQLite for persistence across restarts.
    Operations are isolated per agent_id.
    
    v3 Changes:
    - Unified chat_messages table with 'read' field
    - Removed user_messages and pending_user_messages tables
    - Inbox = unread messages
    """
    
    def __init__(self, agent_id: Optional[str] = None):
        self._repo: Optional[ChatRepository] = None
        self._agent_id = agent_id
        self._sse_subscribers: Dict[str, asyncio.Queue] = {}
        self._log_subscribers: Dict[str, asyncio.Queue] = {}
    
    @property
    def repo(self) -> ChatRepository:
        if self._repo is None:
            self._repo = ChatRepository(get_database())
        return self._repo
    
    @property
    def agent_id(self) -> Optional[str]:
        """Get current agent ID.
        
        Returns:
            The current agent ID, or None if not set.
            
        Note: Returns None instead of fallback to make issues visible.
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
            logger.warning(f"[ChatService] Failed to get current agent ID: {e}")
        return None
    
    def set_agent_id(self, agent_id: str):
        """Set the current agent ID."""
        self._agent_id = agent_id
    
    def _require_agent_id(self, agent_id: Optional[str] = None) -> str:
        """Get agent ID, raising error if not available.
        
        Args:
            agent_id: Optional explicit agent ID
            
        Returns:
            The agent ID to use
            
        Raises:
            ValueError: If no agent ID is available
        """
        aid = agent_id or self.agent_id
        if not aid:
            raise ValueError("No agent ID available. Please select an agent first.")
        return aid
    
    # ==================== Chat Messages ====================
    
    async def get_chat_history(
        self,
        limit: int = 20,
        before_id: Optional[str] = None,
        type_filter: Optional[List[str]] = None,
        summary_length: int = 50,
        agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get chat history with optional summary."""
        aid = self._require_agent_id(agent_id)
        messages = await self.repo.get_messages(
            agent_id=aid,
            limit=min(limit, 100),
            before_id=before_id,
            type_filter=type_filter,
        )
        
        # Create summarized messages if needed
        summarized = []
        for msg in messages:
            content = msg.get("content") or ""
            is_truncated = summary_length > 0 and len(content) > summary_length
            
            summary_msg = {
                "id": msg.get("id"),
                "type": msg.get("type"),
                "timestamp": msg.get("timestamp"),
                "read": msg.get("read", False),
                "summary": content[:summary_length] + "..." if is_truncated else content,
                "is_truncated": is_truncated,
            }
            
            # Include metadata fields
            metadata = msg.get("metadata", {})
            if metadata.get("level"):
                summary_msg["level"] = metadata.get("level")
            if metadata.get("options"):
                summary_msg["options_count"] = len(metadata.get("options"))
            
            summarized.append(summary_msg)
        
        return {
            "success": True,
            "messages": summarized,
            "has_more": len(messages) >= limit,
        }
    
    async def get_chat_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get full content of a specific chat message."""
        return await self.repo.get_message(message_id)
    
    async def add_chat_message(
        self,
        type: str,
        agent_id: Optional[str] = None,
        **data
    ) -> Optional[Dict[str, Any]]:
        """Add a chat message and broadcast to subscribers."""
        aid = self._require_agent_id(agent_id)
        msg_id = data.pop("id", str(uuid4())[:12])
        timestamp = data.pop("timestamp", datetime.now().isoformat())
        content = data.pop("content", data.pop("message", None))
        
        # Save to database
        msg = await self.repo.add_message(
            agent_id=aid,
            id=msg_id,
            type=type,
            content=content,
            metadata=data if data else None,
            timestamp=timestamp,
        )
        
        # Build message for SSE broadcast (include agent_id for filtering)
        broadcast_msg = {
            "id": msg_id,
            "type": type,
            "content": content,
            "timestamp": timestamp,
            "agent_id": aid,  # Include agent_id for client-side filtering
            **data
        }
        
        # Broadcast to SSE subscribers
        await self._broadcast_chat(broadcast_msg)
        
        return msg
    
    async def _broadcast_chat(self, message: Dict[str, Any]):
        """Broadcast message to all chat SSE subscribers."""
        for queue in self._sse_subscribers.values():
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                pass
    
    # ==================== Message Status ====================
    
    async def update_message_status(
        self,
        message_id: str,
        status: str
    ) -> bool:
        """Update message status and broadcast.
        
        For 'read' status, marks the message as read in database.
        """
        if status == "read":
            success = await self.repo.mark_as_read(message_id)
        else:
            # For other statuses, just broadcast (no longer stored)
            success = True
        
        if success:
            # Broadcast status update (not persisted, just for real-time UI)
            status_update = {
                "id": str(uuid4())[:8],
                "type": "STATUS_UPDATE",
                "message_id": message_id,
                "status": status,
                "timestamp": datetime.now().isoformat(),
            }
            await self._broadcast_chat(status_update)
        
        return success
    
    # ==================== Inbox (Unread Messages) ====================
    
    async def get_inbox(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all unread user messages (inbox).
        
        Returns unread messages and marks them as read.
        """
        aid = self._require_agent_id(agent_id)
        messages = await self.repo.get_unread_messages(aid)
        
        # Mark as read and format result
        result = []
        for msg in messages:
            # Mark as read
            await self.repo.mark_as_read(msg["id"])
            
            content = msg.get("content", "")
            result.append({
                "type": "user_message",
                "message_id": msg["id"],
                "content": content,
                "timestamp": msg["timestamp"],
                "priority": "high",
                "summary": f"用户消息: {content[:50]}..." if len(content) > 50 else f"用户消息: {content}",
            })
        
        return result
    
    async def get_unread_count(self, agent_id: Optional[str] = None) -> int:
        """Get count of unread messages."""
        aid = self._require_agent_id(agent_id)
        return await self.repo.get_message_count(aid, read=False)
    
    # ==================== Questions/Responses ====================
    
    async def add_pending_question(
        self,
        question: str,
        options: Optional[List[str]] = None,
        request_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> str:
        """Add a pending question from agent."""
        aid = self._require_agent_id(agent_id)
        request_id = request_id or str(uuid4())[:12]
        
        await self.repo.add_pending_question(
            agent_id=aid,
            request_id=request_id,
            question=question,
            options=options,
        )
        
        # Add to chat messages
        await self.add_chat_message(
            type="AGENT_ASK",
            agent_id=aid,
            id=request_id,
            request_id=request_id,
            question=question,
            options=options,
        )
        
        return request_id
    
    async def get_pending_questions(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all pending questions."""
        aid = self._require_agent_id(agent_id)
        return await self.repo.list_pending_questions(aid)
    
    async def submit_response(
        self,
        request_id: str,
        response: str,
        selected_option: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> bool:
        """Submit user response to a question."""
        aid = self._require_agent_id(agent_id)
        # Check if question exists
        question = await self.repo.get_pending_question(request_id)
        if not question:
            return False
        
        # Add response
        await self.repo.add_question_response(
            agent_id=aid,
            request_id=request_id,
            response=response,
            selected_option=selected_option,
        )
        
        return True
    
    async def check_response(
        self,
        request_id: str
    ) -> Optional[Dict[str, Any]]:
        """Check if user has responded to a question."""
        return await self.repo.pop_question_response(request_id)
    
    async def auto_respond_to_questions(self, response: str, agent_id: Optional[str] = None):
        """Auto-respond to all pending questions with user message."""
        aid = self._require_agent_id(agent_id)
        questions = await self.repo.list_pending_questions(aid)
        for q in questions:
            await self.submit_response(
                request_id=q["request_id"],
                response=response,
                selected_option=None,
                agent_id=aid,
            )
    
    # ==================== Execution Logs ====================
    
    async def add_execution_log(
        self,
        type: str,
        data: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
    ):
        """Add an execution log entry (pure flow log, not associated with messages)."""
        aid = self._require_agent_id(agent_id)
        timestamp = datetime.now().isoformat()
        
        await self.repo.add_execution_log(
            agent_id=aid,
            type=type,
            timestamp=timestamp,
            data=data,
        )
        
        # Broadcast to log subscribers
        log_entry = {
            "type": type,
            "timestamp": timestamp,
            "data": data or {},
        }
        await self._broadcast_log(log_entry)
    
    async def _broadcast_log(self, log: Dict[str, Any]):
        """Broadcast log to all log SSE subscribers."""
        for queue in self._log_subscribers.values():
            try:
                queue.put_nowait(log)
            except asyncio.QueueFull:
                pass
    
    async def get_execution_logs(
        self,
        limit: int = 500,
        agent_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get execution logs."""
        aid = self._require_agent_id(agent_id)
        return await self.repo.list_execution_logs(
            agent_id=aid,
            limit=limit,
        )
    
    async def clear_execution_logs(self, agent_id: Optional[str] = None):
        """Clear all execution logs."""
        aid = self._require_agent_id(agent_id)
        await self.repo.clear_execution_logs(aid)
    
    # ==================== Agent State ====================
    
    async def get_agent_rest_state(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get agent rest state."""
        aid = self._require_agent_id(agent_id)
        return await self.repo.get_agent_rest_state(aid)
    
    async def set_agent_resting(
        self,
        reason: str,
        wake_triggers: Optional[List[Dict]] = None,
        handoff_notes: Optional[str] = None,
        agent_id: Optional[str] = None,
    ):
        """Set agent to resting state."""
        aid = self._require_agent_id(agent_id)
        await self.repo.set_agent_rest_state(aid, {
            "is_resting": True,
            "reason": reason,
            "wake_triggers": wake_triggers or [],
            "handoff_notes": handoff_notes,
            "rest_started": datetime.now().isoformat(),
        })
        
        # Add notification
        await self.add_chat_message(
            type="AGENT_NOTIFY",
            agent_id=aid,
            content=f"💤 进入休息状态: {reason}",
            level="info",
            handoff_notes=handoff_notes,
        )
    
    async def wake_agent(self, reason: str = "Manual wake", agent_id: Optional[str] = None):
        """Wake up the agent."""
        aid = self._require_agent_id(agent_id)
        previous_state = await self.get_agent_rest_state(aid)
        
        await self.repo.set_agent_rest_state(aid, {
            "is_resting": False,
            "reason": None,
            "wake_triggers": [],
            "handoff_notes": None,
            "rest_started": None,
        })
        
        # Add notification
        await self.add_chat_message(
            type="AGENT_NOTIFY",
            agent_id=aid,
            content=f"☀️ 已唤醒: {reason}",
            level="success",
            handoff_notes=previous_state.get("handoff_notes"),
        )
    
    # ==================== SSE Subscription Management ====================
    
    def subscribe_chat(self) -> tuple[str, asyncio.Queue]:
        """Subscribe to chat messages."""
        subscriber_id = str(uuid4())[:8]
        queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        self._sse_subscribers[subscriber_id] = queue
        return subscriber_id, queue
    
    def unsubscribe_chat(self, subscriber_id: str):
        """Unsubscribe from chat messages."""
        self._sse_subscribers.pop(subscriber_id, None)
    
    def subscribe_logs(self) -> tuple[str, asyncio.Queue]:
        """Subscribe to execution logs."""
        subscriber_id = str(uuid4())[:8]
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._log_subscribers[subscriber_id] = queue
        return subscriber_id, queue
    
    def unsubscribe_logs(self, subscriber_id: str):
        """Unsubscribe from execution logs."""
        self._log_subscribers.pop(subscriber_id, None)


# Global instance
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get the global chat service instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service


def set_chat_service_agent(agent_id: str):
    """Set the agent ID for the global chat service."""
    get_chat_service().set_agent_id(agent_id)
