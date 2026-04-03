"""
Compact Engine — 上下文压缩引擎

完整功能（Claude Code 对齐 + NovAIC 原创）:
1. TimeBased MicroCompact — 时间间隔触发的 tool 输出清理
2. MicroCompact — 数量触发的 tool 输出清理
3. Session Memory Compact — 会话记忆独立压缩
4. AutoCompact — 阈值触发的对话摘要压缩
5. ContextCollapse — 渐进式段落坍缩（实验性）
6. Emergency — 紧急压缩 + 暴力截断兜底
7. Post-compact Cleanup — 压缩后回调清理
8. Circuit Breaker — 连续失败熔断
9. Skill-Scoped Compaction — 技能域事务压缩（NovAIC 原创）
"""

from .auto import auto_compact, should_auto_compact
from .cleanup import register_cleanup, run_post_compact_cleanup, clear_cleanup_callbacks
from .collapse import CollapseConfig, CollapseState, ContextCollapse, CollapseTracker
from .micro import micro_compact, CLEARED_MARKER
from .pipeline import CompactPipeline
from .protocols import (
    DefaultTokenCounter,
    NoOpSummarizer,
    Summarizer,
    TokenCounter,
)
from .session_memory import (
    SessionMemory,
    compact_session_memory,
    should_compact_session_memory,
)
from .skill_scoped import SkillScopedCompactor, SkillCheckpoint, SkillPhase
from .time_based import TimeBasedConfig, time_based_micro_compact
from .types import (
    CompactAction,
    CompactConfig,
    CompactResult,
    CompactStage,
    CompactTracking,
    Message,
    MessageRole,
)

__all__ = [
    # Pipeline
    "CompactPipeline",
    # Stages
    "micro_compact",
    "auto_compact",
    "should_auto_compact",
    "time_based_micro_compact",
    "compact_session_memory",
    "should_compact_session_memory",
    # Context Collapse
    "ContextCollapse",
    "CollapseConfig",
    "CollapseState",
    "CollapseTracker",
    # Session Memory
    "SessionMemory",
    # Cleanup
    "register_cleanup",
    "run_post_compact_cleanup",
    "clear_cleanup_callbacks",
    # Protocols
    "Summarizer",
    "TokenCounter",
    "DefaultTokenCounter",
    "NoOpSummarizer",
    # Types
    "CompactConfig",
    "CompactResult",
    "CompactTracking",
    "CompactAction",
    "CompactStage",
    "Message",
    "MessageRole",
    "CLEARED_MARKER",
    # Time-based config
    "TimeBasedConfig",
    # Skill-Scoped (NovAIC original)
    "SkillScopedCompactor",
    "SkillCheckpoint",
    "SkillPhase",
]
