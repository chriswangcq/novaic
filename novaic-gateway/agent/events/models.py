"""
Event Models for NovAIC Agent

Defines the event types, priorities, and data structures for the event-driven architecture.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
import uuid


class EventType(Enum):
    """Event types that the agent can handle."""
    
    # User interactions
    USER_MESSAGE = "user_message"
    SYSTEM_MESSAGE = "system_message"  # System-generated messages (bootstrap, scheduled tasks, etc.)
    
    # Agent to User (Chat MCP)
    AGENT_REPLY = "agent_reply"      # Agent sends a message to user
    AGENT_ASK = "agent_ask"          # Agent asks user a question
    AGENT_NOTIFY = "agent_notify"    # Agent sends notification
    AGENT_IMAGE = "agent_image"      # Agent shows image
    USER_RESPONSE = "user_response"  # User responds to agent's question
    
    # External triggers
    WECHAT_MESSAGE = "wechat_message"
    CRON_TRIGGER = "cron_trigger"
    WEBHOOK = "webhook"
    FILE_CHANGE = "file_change"
    
    # Internal events
    SUBAGENT_RESULT = "subagent_result"
    SUBAGENT_PROGRESS = "subagent_progress"
    
    # Task events (unified task system)
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    # System events
    SYSTEM = "system"
    WAKE_REQUEST = "wake_request"
    STATE_CHANGE = "state_change"


class EventPriority(Enum):
    """Event priorities for queue ordering."""
    
    CRITICAL = 0    # System critical events (errors, shutdowns)
    HIGH = 1        # Direct user interactions
    NORMAL = 2      # Standard events (webhooks, triggers)
    LOW = 3         # Background tasks
    BACKGROUND = 4  # Lowest priority tasks


@dataclass
class AgentEvent:
    """
    Represents an event in the agent's event-driven system.
    
    Events are the primary way to communicate with the agent.
    All inputs (user messages, triggers, etc.) are converted to events
    and processed through the EventBus.
    """
    
    # Required fields
    type: EventType
    source: str  # Event source identifier (e.g., "user", "cron:daily_report")
    payload: Dict[str, Any]  # Event-specific data
    
    # Auto-generated fields
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    
    # Optional fields
    priority: EventPriority = EventPriority.NORMAL
    session_id: Optional[str] = None  # Target session (if applicable)
    reply_channel: Optional[str] = None  # Where to send responses
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other: "AgentEvent") -> bool:
        """Compare events for priority queue ordering."""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.timestamp < other.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "reply_channel": self.reply_channel,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentEvent":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())[:12]),
            type=EventType(data["type"]),
            source=data["source"],
            payload=data["payload"],
            priority=EventPriority(data.get("priority", EventPriority.NORMAL.value)),
            timestamp=data.get("timestamp", datetime.now().timestamp()),
            session_id=data.get("session_id"),
            reply_channel=data.get("reply_channel"),
            metadata=data.get("metadata", {}),
        )
    
    @classmethod
    def user_message(
        cls,
        content: str,
        session_id: Optional[str] = None,
        reply_channel: Optional[str] = None,
        **kwargs
    ) -> "AgentEvent":
        """Create a user message event."""
        return cls(
            type=EventType.USER_MESSAGE,
            source="user",
            payload={"content": content, **kwargs},
            priority=EventPriority.HIGH,
            session_id=session_id,
            reply_channel=reply_channel,
        )
    
    @classmethod
    def cron_trigger(
        cls,
        trigger_id: str,
        trigger_name: str,
        message: str,
        **kwargs
    ) -> "AgentEvent":
        """Create a cron trigger event."""
        return cls(
            type=EventType.CRON_TRIGGER,
            source=f"cron:{trigger_id}",
            payload={
                "trigger_id": trigger_id,
                "trigger_name": trigger_name,
                "message": message,
                **kwargs
            },
            priority=EventPriority.NORMAL,
        )
    
    @classmethod
    def webhook(
        cls,
        webhook_name: str,
        data: Dict[str, Any],
        **kwargs
    ) -> "AgentEvent":
        """Create a webhook event."""
        return cls(
            type=EventType.WEBHOOK,
            source=f"webhook:{webhook_name}",
            payload={"webhook_name": webhook_name, "data": data, **kwargs},
            priority=EventPriority.NORMAL,
        )
    
    @classmethod
    def subagent_result(
        cls,
        subagent_id: str,
        result: Dict[str, Any],
        parent_session_id: str,
        **kwargs
    ) -> "AgentEvent":
        """Create a subagent result event."""
        return cls(
            type=EventType.SUBAGENT_RESULT,
            source=f"subagent:{subagent_id}",
            payload={
                "subagent_id": subagent_id,
                "result": result,
                **kwargs
            },
            priority=EventPriority.HIGH,
            session_id=parent_session_id,
        )
    
    @classmethod
    def agent_reply(
        cls,
        message: str,
        attachments: list = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> "AgentEvent":
        """Create an agent reply event (agent sends message to user)."""
        return cls(
            type=EventType.AGENT_REPLY,
            source="agent",
            payload={
                "message": message,
                "attachments": attachments or [],
                "reply_type": "message",
                **kwargs
            },
            priority=EventPriority.HIGH,
            session_id=session_id,
        )
    
    @classmethod
    def agent_ask(
        cls,
        question: str,
        options: list = None,
        request_id: str = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> "AgentEvent":
        """Create an agent ask event (agent asks user a question)."""
        return cls(
            type=EventType.AGENT_ASK,
            source="agent",
            payload={
                "question": question,
                "options": options,
                "request_id": request_id or str(uuid.uuid4())[:12],
                "reply_type": "question",
                **kwargs
            },
            priority=EventPriority.HIGH,
            session_id=session_id,
        )
    
    @classmethod
    def agent_notify(
        cls,
        message: str,
        level: str = "info",
        session_id: Optional[str] = None,
        **kwargs
    ) -> "AgentEvent":
        """Create an agent notification event."""
        return cls(
            type=EventType.AGENT_NOTIFY,
            source="agent",
            payload={
                "message": message,
                "level": level,
                "reply_type": "notification",
                **kwargs
            },
            priority=EventPriority.NORMAL,
            session_id=session_id,
        )
    
    @classmethod
    def task_completed(
        cls,
        task_id: str,
        task_type: str,
        label: str,
        summary: str,
        parent_session_key: Optional[str] = None,
        **kwargs
    ) -> "AgentEvent":
        """Create a task completed event."""
        return cls(
            type=EventType.TASK_COMPLETED,
            source=f"task:{task_id}",
            payload={
                "task_id": task_id,
                "type": task_type,
                "label": label,
                "status": "completed",
                "summary": summary,
                "parent_session_key": parent_session_key,
                **kwargs
            },
            priority=EventPriority.HIGH,
            session_id=parent_session_key,
        )
    
    @classmethod
    def task_failed(
        cls,
        task_id: str,
        task_type: str,
        label: str,
        error: str,
        parent_session_key: Optional[str] = None,
        **kwargs
    ) -> "AgentEvent":
        """Create a task failed event."""
        return cls(
            type=EventType.TASK_FAILED,
            source=f"task:{task_id}",
            payload={
                "task_id": task_id,
                "type": task_type,
                "label": label,
                "status": "failed",
                "error": error,
                "parent_session_key": parent_session_key,
                **kwargs
            },
            priority=EventPriority.HIGH,
            session_id=parent_session_key,
        )


@dataclass
class EventResult:
    """Result of processing an event."""
    
    event_id: str
    success: bool
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "success": self.success,
            "response": self.response,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }
