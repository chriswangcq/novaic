"""
WebhookAdapter - Converts webhook calls to AgentEvents
"""

from typing import Dict, Any, Optional
from ..models import AgentEvent, EventType, EventPriority


class WebhookAdapter:
    """
    Adapter for converting webhook HTTP requests to AgentEvents.
    """
    
    def to_event(
        self,
        webhook_name: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> AgentEvent:
        """
        Convert a webhook call to an AgentEvent.
        
        Args:
            webhook_name: Name/identifier of the webhook
            data: Webhook payload data
            headers: HTTP headers (optional)
            session_id: Target session ID
            priority: Event priority
        
        Returns:
            AgentEvent ready for publishing
        """
        return AgentEvent(
            type=EventType.WEBHOOK,
            source=f"webhook:{webhook_name}",
            payload={
                "webhook_name": webhook_name,
                "data": data,
            },
            priority=priority,
            session_id=session_id,
            metadata={
                "headers": headers or {},
            }
        )
    
    def from_http_request(
        self,
        webhook_name: str,
        request_body: Dict[str, Any],
        headers: Dict[str, str],
    ) -> AgentEvent:
        """
        Create an event from an HTTP webhook request.
        
        Args:
            webhook_name: The webhook endpoint name
            request_body: Parsed JSON body
            headers: HTTP headers
        
        Returns:
            AgentEvent
        """
        # Determine priority from headers if specified
        priority_str = headers.get("X-Priority", "normal").lower()
        priority_map = {
            "critical": EventPriority.CRITICAL,
            "high": EventPriority.HIGH,
            "normal": EventPriority.NORMAL,
            "low": EventPriority.LOW,
        }
        priority = priority_map.get(priority_str, EventPriority.NORMAL)
        
        # Get session ID from headers if specified
        session_id = headers.get("X-Session-Id")
        
        return self.to_event(
            webhook_name=webhook_name,
            data=request_body,
            headers=headers,
            session_id=session_id,
            priority=priority,
        )
