"""
Context Stack — A unified context + memory + skill engine for AI agents.

    engine.run(skill, messages)       → full lifecycle
    engine.run_meta(messages, task)   → scoped execution without skill
    engine.run_recall(messages, query) → memory exploration with tools
    engine.match(task)                → find the right skill
    engine.status()                   → inspect state
"""

__version__ = "0.2.0"

# Engine
from .engine import ContextEngine

# Context types
from .context.types import (
    Message,
    MessageRole,
    ScopeRecord,
    ScopeState,
    CompactConfig,
    CompactAction,
    CompactResult,
    StackStatus,
    LifecycleResult,
)

# Skill types
from .skill.types import Skill, SkillType
from .skill.registry import SkillRegistry
from .skill.builtins.meta import MetaSkill
from .skill.builtins.recall import RecallSkill

# Protocols
from .protocols import AgentExecutor, Summarizer, TokenCounter, MemoryBackend

# Memory
from .memory.store import MemoryScopeStore

# Tool Router (Fix #3)
from .tool_router import RecallToolRouter

# Hooks
from .hooks import HookRegistry

__all__ = [
    "ContextEngine",
    # Types
    "Message", "MessageRole",
    "ScopeRecord", "ScopeState",
    "CompactConfig", "CompactAction", "CompactResult",
    "StackStatus", "LifecycleResult",
    # Skill
    "Skill", "SkillType",
    "SkillRegistry",
    "MetaSkill", "RecallSkill",
    # Protocols
    "AgentExecutor", "Summarizer", "TokenCounter", "MemoryBackend",
    # Memory
    "MemoryScopeStore",
    # Tool Router
    "RecallToolRouter",
    # Hooks
    "HookRegistry",
]
