"""
Database Repositories

Data access layer implementing the Repository pattern.
All database operations go through these classes.

v12: Added RuntimeRepository for Master-driven Agent Runtime management.
v14: Added SubAgentRepository for SubAgent state management.
v15: Three-Task Architecture - pipeline_tasks based system.
v16: Removed v11 legacy (ActionTaskRepository, MCPExecutionRepository, WorkerRepository).
"""

from .config import ConfigRepository
from .agent import AgentRepository
from .session import SessionRepository
from .chat import ChatRepository
from .agent_state import AgentStateRepository
from .memory import MemoryRepository
from .notebook import NotebookRepository
from .drive import DriveRepository
from .skill import SkillRepository
from .message import MessageRepository
from .runtime import RuntimeRepository, AgentRuntime
from .subagent import SubAgentRepository, SubAgent
from gateway.db.access import get_db


def get_message_repo(db=None) -> MessageRepository:
    db = db or get_db()
    return MessageRepository(db)


def get_agent_state_repo(db=None) -> AgentStateRepository:
    db = db or get_db()
    return AgentStateRepository(db)

__all__ = [
    "ConfigRepository",
    "AgentRepository",
    "SessionRepository",
    "ChatRepository",
    "AgentStateRepository",
    "MemoryRepository",
    "NotebookRepository",
    "DriveRepository",
    "SkillRepository",
    "MessageRepository",
    "RuntimeRepository",
    "AgentRuntime",
    "SubAgentRepository",
    "SubAgent",
    "get_message_repo",
    "get_agent_state_repo",
]
