"""
Chat Service - Database-backed Chat State Management

Handles all chat-related operations using SQLite for state management.
This replaces the in-memory state variables in main.py.
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
    """
    
    def __init__(self):
        self._repo: Optional[ChatRepository] = None
        self._sse_subscribers: Dict[str, asyncio.Queue] = {}
        self._log_subscribers: Dict[str, asyncio.Queue] = {}
    
    @property
    def repo(self) -> ChatRepository:
        if self._repo is None:
            self._repo = ChatRepository(get_database())
        return self._repo
    
    # ==================== Chat Messages ====================
    
    async def get_chat_history(
        self,
        limit: int = 20,
        before_id: Optional[str] = None,
        message_type: Optional[str] = None,
        summary_length: int = 50,
    ) -> Dict[str, Any]:
        """Get chat history with optional summary."""
        messages = await self.repo.list_chat_messages(
            limit=min(limit, 100),
            before_id=before_id,
            message_type=message_type,
        )
        
        # Create summarized messages if needed
        summarized = []
        for msg in messages:
            content = msg.get("message") or msg.get("question") or ""
            is_truncated = summary_length > 0 and len(content) > summary_length
            
            summary_msg = {
                "id": msg.get("id"),
                "type": msg.get("type"),
                "timestamp": msg.get("timestamp"),
                "summary": content[:summary_length] + "..." if is_truncated else content,
                "is_truncated": is_truncated,
            }
            if msg.get("level"):
                summary_msg["level"] = msg.get("level")
            if msg.get("options"):
                summary_msg["options_count"] = len(msg.get("options"))
            
            summarized.append(summary_msg)
        
        return {
            "success": True,
            "messages": summarized,
            "has_more": len(messages) >= limit,
        }
    
    async def get_chat_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get full content of a specific chat message."""
        return await self.repo.get_chat_message(message_id)
    
    async def add_chat_message(
        self,
        type: str,
        **data
    ) -> Dict[str, Any]:
        """Add a chat message and broadcast to subscribers."""
        msg_id = data.pop("id", str(uuid4())[:12])
        timestamp = data.pop("timestamp", datetime.now().isoformat())
        
        # Save to database
        msg = await self.repo.add_chat_message(
            id=msg_id,
            type=type,
            timestamp=timestamp,
            **data
        )
        
        # Broadcast to SSE subscribers
        await self._broadcast_chat(msg)
        
        return msg
    
    async def _broadcast_chat(self, message: Dict[str, Any]):
        """Broadcast message to all chat SSE subscribers."""
        for queue in self._sse_subscribers.values():
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                pass
    
    # ==================== User Messages ====================
    
    async def add_user_message(
        self,
        content: str,
        model: Optional[str] = None,
        api_key_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a user message."""
        msg_id = str(uuid4())[:12]
        timestamp = datetime.now().isoformat()
        
        # Save to user_messages table
        user_msg = await self.repo.add_user_message(
            id=msg_id,
            content=content,
            timestamp=timestamp,
            status="delivered",
            model=model,
            api_key_id=api_key_id,
        )
        
        # Also add to chat_messages for display
        chat_msg = await self.add_chat_message(
            type="USER_MESSAGE",
            id=msg_id,
            timestamp=timestamp,
            content=content,
        )
        
        return {
            "message_id": msg_id,
            "timestamp": timestamp,
            "status": "delivered",
        }
    
    async def update_message_status(
        self,
        message_id: str,
        status: str
    ) -> bool:
        """Update message status and broadcast."""
        success = await self.repo.update_user_message_status(message_id, status)
        
        if success:
            # Broadcast status update
            status_update = {
                "id": str(uuid4())[:8],
                "type": "STATUS_UPDATE",
                "message_id": message_id,
                "status": status,
                "timestamp": datetime.now().isoformat(),
            }
            await self._broadcast_chat(status_update)
        
        return success
    
    # ==================== Pending User Messages (Inbox) ====================
    
    async def add_to_inbox(
        self,
        message_id: str,
        content: str,
        model: Optional[str] = None,
        api_key_id: Optional[str] = None,
    ):
        """Add a message to the pending inbox."""
        await self.repo.add_pending_user_message(
            id=message_id,
            content=content,
            timestamp=datetime.now().isoformat(),
            model=model,
            api_key_id=api_key_id,
        )
    
    async def get_inbox(self) -> List[Dict[str, Any]]:
        """Get all pending user messages."""
        messages = await self.repo.list_pending_user_messages()
        
        # Mark as read and remove from pending
        result = []
        for msg in messages:
            # Update status to read
            await self.update_message_status(msg["id"], "read")
            
            # Remove from pending
            await self.repo.pop_pending_user_message(msg["id"])
            
            result.append({
                "type": "user_message",
                "message_id": msg["id"],
                "content": msg["content"],
                "timestamp": msg["timestamp"],
                "priority": "high",
                "summary": f"用户消息: {msg['content'][:50]}...",
            })
        
        return result
    
    # ==================== Questions/Responses ====================
    
    async def add_pending_question(
        self,
        question: str,
        options: Optional[List[str]] = None,
        request_id: Optional[str] = None,
    ) -> str:
        """Add a pending question from agent."""
        request_id = request_id or str(uuid4())[:12]
        
        await self.repo.add_pending_question(
            request_id=request_id,
            question=question,
            options=options,
        )
        
        # Add to chat messages
        await self.add_chat_message(
            type="AGENT_ASK",
            id=request_id,
            request_id=request_id,
            question=question,
            options=options,
        )
        
        return request_id
    
    async def get_pending_questions(self) -> List[Dict[str, Any]]:
        """Get all pending questions."""
        return await self.repo.list_pending_questions()
    
    async def submit_response(
        self,
        request_id: str,
        response: str,
        selected_option: Optional[str] = None,
    ) -> bool:
        """Submit user response to a question."""
        # Check if question exists
        question = await self.repo.get_pending_question(request_id)
        if not question:
            return False
        
        # Add response
        await self.repo.add_question_response(
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
    
    async def auto_respond_to_questions(self, response: str):
        """Auto-respond to all pending questions with user message."""
        questions = await self.repo.list_pending_questions()
        for q in questions:
            await self.submit_response(
                request_id=q["request_id"],
                response=response,
                selected_option=None,
            )
    
    # ==================== Execution Logs ====================
    
    async def add_execution_log(
        self,
        type: str,
        data: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None,
    ):
        """Add an execution log entry."""
        timestamp = datetime.now().isoformat()
        
        await self.repo.add_execution_log(
            type=type,
            timestamp=timestamp,
            data=data,
            message_id=message_id,
        )
        
        # Broadcast to log subscribers
        log_entry = {
            "type": type,
            "timestamp": timestamp,
            "data": data or {},
            "message_id": message_id,
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
        message_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get execution logs."""
        return await self.repo.list_execution_logs(
            limit=limit,
            message_id=message_id,
        )
    
    async def clear_execution_logs(self):
        """Clear all execution logs."""
        await self.repo.clear_execution_logs()
    
    # ==================== Agent State ====================
    
    async def get_agent_rest_state(self) -> Dict[str, Any]:
        """Get agent rest state."""
        return await self.repo.get_agent_rest_state()
    
    async def set_agent_resting(
        self,
        reason: str,
        wake_triggers: Optional[List[Dict]] = None,
        handoff_notes: Optional[str] = None,
    ):
        """Set agent to resting state."""
        await self.repo.set_agent_rest_state(
            is_resting=True,
            reason=reason,
            wake_triggers=wake_triggers or [],
            handoff_notes=handoff_notes,
            rest_started=datetime.now().isoformat(),
        )
        
        # Add notification
        await self.add_chat_message(
            type="AGENT_NOTIFY",
            message=f"💤 进入休息状态: {reason}",
            level="info",
            handoff_notes=handoff_notes,
        )
    
    async def wake_agent(self, reason: str = "Manual wake"):
        """Wake up the agent."""
        previous_state = await self.get_agent_rest_state()
        
        await self.repo.clear_agent_rest_state()
        
        # Add notification
        await self.add_chat_message(
            type="AGENT_NOTIFY",
            message=f"☀️ 已唤醒: {reason}",
            level="success",
            handoff_notes=previous_state.get("handoff_notes"),
        )
    
    async def is_agent_busy(self) -> bool:
        """Check if agent is busy."""
        return await self.repo.is_agent_busy()
    
    async def set_agent_busy(self, busy: bool):
        """Set agent busy state."""
        await self.repo.set_agent_busy(busy)
    
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
