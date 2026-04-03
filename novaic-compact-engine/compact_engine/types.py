"""
Compact Engine — Core Types

上下文压缩引擎的数据结构。
不依赖任何外部框架，集成方只需映射到这些类型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_RESULT = "tool_result"


class CompactStage(str, Enum):
    """压缩阶段"""
    MICRO = "micro"             # 清理旧 tool output
    AUTO = "auto"               # 阈值触发的自动摘要
    REACTIVE = "reactive"       # API prompt_too_long 后的紧急压缩
    MANUAL = "manual"           # 用户手动触发


class CompactAction(str, Enum):
    """压缩动作"""
    SKIP = "skip"               # 不需要压缩
    PRUNE_TOOL_OUTPUTS = "prune_tool_outputs"  # 清理 tool 输出
    SUMMARIZE = "summarize"     # 摘要压缩
    EMERGENCY = "emergency"     # 紧急全量压缩


@dataclass
class Message:
    """
    消息 — 最小公共结构
    
    集成方需将自己的消息格式映射到此类型。
    仅保留压缩引擎必需的字段。
    """
    role: MessageRole
    content: str
    token_count: int = 0        # 预计算的 token 数（0 表示未计算）
    tool_name: Optional[str] = None    # tool_result 的工具名
    tool_id: Optional[str] = None      # tool_result 的调用 ID
    timestamp: float = 0.0     # Unix timestamp
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_tool_output(self) -> bool:
        return self.role == MessageRole.TOOL_RESULT or self.tool_name is not None


@dataclass(frozen=True)
class CompactResult:
    """压缩操作的结果"""
    stage: CompactStage
    action: CompactAction
    messages: List[Message]         # 压缩后的消息列表
    tokens_before: int
    tokens_after: int
    summary: str = ""               # 摘要文本（如果执行了 summarize）
    pruned_tool_ids: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def tokens_saved(self) -> int:
        return self.tokens_before - self.tokens_after

    @property
    def success(self) -> bool:
        return self.error is None


@dataclass
class CompactConfig:
    """
    压缩引擎配置
    
    所有阈值均可动态调整，支持运行时 override。
    """
    # ── 上下文窗口 ──
    context_window: int = 200_000        # 模型上下文窗口大小
    max_output_tokens: int = 16_000      # 模型最大输出 token

    # ── MicroCompact ──
    micro_compactable_tools: List[str] = field(default_factory=lambda: [
        "file_read", "bash", "grep", "glob", "web_fetch", "web_search",
        "file_edit", "file_write",
    ])
    micro_keep_recent: int = 3           # 保留最近 N 个 tool 输出
    micro_min_tool_tokens: int = 200     # 低于此值不清理

    # ── AutoCompact ──
    auto_buffer_tokens: int = 13_000     # 触发缓冲
    auto_max_summary_tokens: int = 20_000  # 摘要最大 token

    # ── 熔断器 ──
    max_consecutive_failures: int = 3    # 连续失败后停止重试

    # ── Emergency ──
    emergency_buffer_tokens: int = 3_000  # 紧急模式缓冲

    @property
    def effective_window(self) -> int:
        """可用上下文 = 窗口 - 输出预留"""
        return self.context_window - min(self.max_output_tokens, 20_000)

    @property
    def auto_threshold(self) -> int:
        """AutoCompact 触发阈值"""
        return self.effective_window - self.auto_buffer_tokens

    @property
    def emergency_threshold(self) -> int:
        """紧急压缩阈值"""
        return self.effective_window - self.emergency_buffer_tokens


@dataclass
class CompactTracking:
    """
    会话级压缩追踪状态
    
    存活于整个会话期间，跨多轮对话。
    """
    compacted: bool = False
    turn_counter: int = 0
    consecutive_failures: int = 0       # 连续失败计数（熔断器）
    total_tokens_saved: int = 0         # 本会话累计节省
    compact_count: int = 0              # 本会话压缩次数
