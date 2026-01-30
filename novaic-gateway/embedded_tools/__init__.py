"""
Embedded MCP Tools

These tools run directly within the Gateway process, eliminating the need
for separate MCP service processes and ports.

Tools are organized by category:
- session: Agent context and self-management tools
- local: Host-side web search and fetch tools
- memory: Persistent memory and state management
- chat: Agent-user communication tools
"""

from .session import (
    agent_context_list,
    agent_context_history,
    agent_context_send,
    agent_inbox,
    agent_rest,
)

from .local import (
    web_search,
    web_fetch,
)

from .memory import (
    memory_save,
    memory_recall,
    memory_delete,
    memory_list_namespaces,
    task_log,
    task_history,
    goal_set,
    goal_progress,
    goal_complete,
    session_state,
)

from .chat import (
    chat_reply,
    chat_ask,
    chat_notify,
    chat_show_image,
    chat_history,
    chat_get_message,
)

# All embedded tools for registration
ALL_TOOLS = [
    # Session tools
    agent_context_list,
    agent_context_history,
    agent_context_send,
    agent_inbox,
    agent_rest,
    # Local tools
    web_search,
    web_fetch,
    # Memory tools
    memory_save,
    memory_recall,
    memory_delete,
    memory_list_namespaces,
    task_log,
    task_history,
    goal_set,
    goal_progress,
    goal_complete,
    session_state,
    # Chat tools
    chat_reply,
    chat_ask,
    chat_notify,
    chat_show_image,
    chat_history,
    chat_get_message,
]

__all__ = [
    # Session
    "agent_context_list",
    "agent_context_history", 
    "agent_context_send",
    "agent_inbox",
    "agent_rest",
    # Local
    "web_search",
    "web_fetch",
    # Memory
    "memory_save",
    "memory_recall",
    "memory_delete",
    "memory_list_namespaces",
    "task_log",
    "task_history",
    "goal_set",
    "goal_progress",
    "goal_complete",
    "session_state",
    # Chat
    "chat_reply",
    "chat_ask",
    "chat_notify",
    "chat_show_image",
    "chat_history",
    "chat_get_message",
    # Collection
    "ALL_TOOLS",
]
