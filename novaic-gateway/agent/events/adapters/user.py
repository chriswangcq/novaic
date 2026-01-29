"""
UserMessageAdapter - Converts HTTP/WebSocket user messages to AgentEvents
"""

from typing import Dict, Any, Optional
from ..models import AgentEvent, EventType, EventPriority


class UserMessageAdapter:
    """
    Adapter for converting user messages from HTTP/WebSocket to AgentEvents.
    """
    
    def __init__(self, default_session_id: str = "main"):
        """
        Initialize the adapter.
        
        Args:
            default_session_id: Default session ID if not specified
        """
        self.default_session_id = default_session_id
    
    def to_event(
        self,
        content: str,
        session_id: Optional[str] = None,
        reply_channel: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentEvent:
        """
        Convert a user message to an AgentEvent.
        
        Args:
            content: The message content
            session_id: Session ID (uses default if not specified)
            reply_channel: Channel for response routing (e.g., "http", "websocket")
            metadata: Additional metadata
            **kwargs: Additional payload fields
        
        Returns:
            AgentEvent ready for publishing
        """
        return AgentEvent(
            type=EventType.USER_MESSAGE,
            source="user",
            payload={
                "content": content,
                **kwargs
            },
            priority=EventPriority.HIGH,
            session_id=session_id or self.default_session_id,
            reply_channel=reply_channel,
            metadata=metadata or {},
        )
    
    def from_http_request(
        self,
        request_data: Dict[str, Any],
        reply_channel: str = "http"
    ) -> AgentEvent:
        """
        Create an event from HTTP request data.
        
        Expected request_data format:
        {
            "message": "user message content",
            "session_id": "optional session id",
            "model": "optional model override",
            ...
        }
        """
        return self.to_event(
            content=request_data.get("message", ""),
            session_id=request_data.get("session_id"),
            reply_channel=reply_channel,
            metadata={
                "model": request_data.get("model"),
                "provider": request_data.get("provider"),
            }
        )
    
    def from_websocket_message(
        self,
        ws_message: Dict[str, Any],
        client_id: str,
        reply_channel: str = "websocket"
    ) -> AgentEvent:
        """
        Create an event from WebSocket message.
        
        Expected ws_message format:
        {
            "type": "chat",
            "data": {
                "message": "user message",
                ...
            }
        }
        """
        data = ws_message.get("data", {})
        
        return self.to_event(
            content=data.get("message", ""),
            session_id=data.get("session_id"),
            reply_channel=f"{reply_channel}:{client_id}",
            metadata={
                "client_id": client_id,
                "ws_message_type": ws_message.get("type"),
            }
        )
