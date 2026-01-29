"""Event adapters for converting external inputs to AgentEvents."""

from .user import UserMessageAdapter
from .webhook import WebhookAdapter

__all__ = ["UserMessageAdapter", "WebhookAdapter"]
