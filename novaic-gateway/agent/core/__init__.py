"""Agent core module - state management."""

# Only export state management here
# NovAICAgent is in core/agent.py (not agent/core/) to avoid circular imports
# Import directly: from core.agent import NovAICAgent
from .state import AgentState, StateManager

__all__ = [
    "AgentState",
    "StateManager",
]
