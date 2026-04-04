"""
Context Stack v2 — Passive, host-driven context engine.

    engine.prepare_messages_for_llm(messages)  → budget-aware messages
    engine.match(task)                          → find the right skill
    engine.status(messages)                     → inspect state
    engine.close()                              → release resources

    # Tool-driven scope management (via SkillToolRouter):
    engine.router.dispatch(tool_name, args, messages)
    skill_begin / skill_end                     → model controls the stack
"""

__version__ = "2.0.0-alpha.6"

from .types import (
    Message,
    MessageRole,
    ScopeRecord,
    ScopeState,
    ScopePhase,
    StackFrame,
    TurnContext,
    TurnPayload,
    CompactAction,
    CompactResult,
    StackStatus,
    LifecycleResult,
)
from .config import CompactConfig
from .protocols import Summarizer, TokenCounter, MemoryBackend, SkillEndReportValidator
from .engine import ContextEngine
from .stack import SkillStack
from .tool_router import SkillToolRouter, ToolResult
from .recall import RecallSkill
from .hooks import HookRegistry
from .defaults import CharTokenCounter, TiktokenCounter, StubSummarizer, InMemoryScopeStore
from .blob import (
    CheckpointBlobError,
    BlobVersionError,
    BlobConfigHashError,
    BlobCorruptedError,
    compute_config_hash,
    compute_blob_hash,
    BLOB_VERSION,
)

from .sqlite_store import SqliteScopeStore
from .novaic_adapter import (
    create_engine_for_novaic,
    novaic_msg_to_v2,
    v2_msg_to_novaic,
    convert_messages,
    export_messages,
    SkillRegistryAdapter,
    NovAICSummarizerAdapter,
)

from .fuser import ScopeFuser

__all__ = [
    "ContextEngine",
    # Types
    "Message", "MessageRole",
    "ScopeRecord", "ScopeState", "ScopePhase",
    "StackFrame", "TurnContext", "TurnPayload",
    "CompactAction", "CompactResult",
    "StackStatus", "LifecycleResult",
    # Config
    "CompactConfig",
    # Protocols
    "Summarizer", "TokenCounter", "MemoryBackend", "SkillEndReportValidator",
    # Stack
    "SkillStack",
    # Tool Router (M2)
    "SkillToolRouter", "ToolResult",
    # Recall (M2)
    "RecallSkill",
    # Hooks (M2)
    "HookRegistry",
    # Checkpoint Blob (M3)
    "CheckpointBlobError", "BlobVersionError",
    "BlobConfigHashError", "BlobCorruptedError",
    "compute_config_hash", "compute_blob_hash",
    "BLOB_VERSION",
    # SQLite Store (M4)
    "SqliteScopeStore",
    # NovAIC Adapter (M4)
    "create_engine_for_novaic",
    "novaic_msg_to_v2", "v2_msg_to_novaic",
    "convert_messages", "export_messages",
    "SkillRegistryAdapter", "NovAICSummarizerAdapter",
    # Gem Fusion (消消乐)
    "ScopeFuser",
    # Defaults
    "CharTokenCounter", "TiktokenCounter",
    "StubSummarizer", "InMemoryScopeStore",
]
