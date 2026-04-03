"""
Compact Engine — Context Collapse (上下文坍缩)

借鉴 Claude Code contextCollapse（实验性功能）:
- 90% 容量时开始 commit（标记可丢弃的旧上下文段）
- 95% 容量时 blocking（阻止新消息直到压缩完成）
- 与 AutoCompact 互斥（坍缩是更精细的替代方案）
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

from .protocols import DefaultTokenCounter, TokenCounter
from .types import (
    CompactAction,
    CompactConfig,
    CompactResult,
    CompactStage,
    Message,
    MessageRole,
)

logger = logging.getLogger("compact_engine.collapse")


class CollapseState(str, Enum):
    IDLE = "idle"                 # 正常运行
    COMMITTING = "committing"     # 正在标记可丢弃的段
    BLOCKING = "blocking"         # 阻塞等待压缩完成


# 阈值常量（相对于 effective_window 的百分比）
COMMIT_THRESHOLD = 0.90            # 90% 开始 commit
BLOCKING_THRESHOLD = 0.95          # 95% 开始 blocking


@dataclass
class CollapseConfig:
    """上下文坍缩配置"""
    enabled: bool = False             # 默认关闭（实验性）
    commit_pct: float = COMMIT_THRESHOLD
    blocking_pct: float = BLOCKING_THRESHOLD
    min_segment_messages: int = 4     # 至少 4 条消息才能构成一个 segment


@dataclass
class CollapseSegment:
    """
    可坍缩的消息段

    一个 segment 是一组连续的消息，代表一个完整的交互轮次。
    commit 时标记 segment 为可丢弃，collapse 时移除。
    """
    start_idx: int
    end_idx: int
    token_count: int
    committed: bool = False


@dataclass
class CollapseTracker:
    """上下文坍缩状态追踪"""
    state: CollapseState = CollapseState.IDLE
    segments: List[CollapseSegment] = field(default_factory=list)
    committed_tokens: int = 0          # 已 commit 的 token 总量
    collapsed_count: int = 0           # 已坍缩次数

    def reset(self) -> None:
        self.state = CollapseState.IDLE
        self.segments.clear()
        self.committed_tokens = 0


class ContextCollapse:
    """
    上下文坍缩管理器
    
    工作流：
    1. evaluate() — 每轮对话后评估当前容量
    2. 如果达到 90%，标记旧 segments 为 committed
    3. 如果达到 95%，触发 collapse（移除 committed segments）
    4. 提供摘要（通过 Summarizer 生成）代替被移除的段
    
    与 AutoCompact 的区别：
    - AutoCompact 一次性压缩所有旧消息
    - ContextCollapse 更精细，按 segment 渐进式丢弃
    - 保留更多细节（只丢弃最旧的 committed 段）
    """

    def __init__(
        self,
        config: Optional[CollapseConfig] = None,
        compact_config: Optional[CompactConfig] = None,
        counter: Optional[TokenCounter] = None,
    ):
        self._config = config or CollapseConfig()
        self._compact_config = compact_config or CompactConfig()
        self._counter = counter or DefaultTokenCounter()
        self.tracker = CollapseTracker()

    @property
    def enabled(self) -> bool:
        return self._config.enabled

    def evaluate(
        self,
        messages: List[Message],
    ) -> Tuple[CollapseState, Optional[CompactResult]]:
        """
        评估当前上下文状态并执行必要操作。
        
        Returns:
            (当前状态, 压缩结果（如果触发了 collapse）)
        """
        if not self._config.enabled:
            return CollapseState.IDLE, None

        total_tokens = self._counter.count_messages(messages)
        effective = self._compact_config.effective_window
        usage_pct = total_tokens / effective if effective > 0 else 0

        # 更新 segments
        self._update_segments(messages)

        if usage_pct >= self._config.blocking_pct:
            # 95%: 触发 collapse
            self.tracker.state = CollapseState.BLOCKING
            result = self._collapse(messages, total_tokens)
            return CollapseState.BLOCKING, result

        elif usage_pct >= self._config.commit_pct:
            # 90%: 标记 commit
            self.tracker.state = CollapseState.COMMITTING
            self._commit_oldest_segments()
            logger.info(
                "[Collapse] Committing: %.1f%% capacity, %d tokens committed",
                usage_pct * 100,
                self.tracker.committed_tokens,
            )
            return CollapseState.COMMITTING, None

        else:
            self.tracker.state = CollapseState.IDLE
            return CollapseState.IDLE, None

    def _update_segments(self, messages: List[Message]) -> None:
        """将消息划分为 segments（按 user→assistant 轮次）"""
        self.tracker.segments.clear()
        current_start = 0
        current_tokens = 0

        for i, msg in enumerate(messages):
            current_tokens += msg.token_count or self._counter.count(msg.content)

            # 一个完整轮次结束：assistant 消息后跟 user 消息
            is_turn_end = (
                msg.role == MessageRole.ASSISTANT
                and i + 1 < len(messages)
                and messages[i + 1].role == MessageRole.USER
            )
            is_last = (i == len(messages) - 1)

            if is_turn_end or is_last:
                if i - current_start + 1 >= self._config.min_segment_messages:
                    self.tracker.segments.append(CollapseSegment(
                        start_idx=current_start,
                        end_idx=i,
                        token_count=current_tokens,
                    ))
                current_start = i + 1
                current_tokens = 0

    def _commit_oldest_segments(self) -> None:
        """标记最旧的未 commit 段"""
        committed = 0
        for seg in self.tracker.segments:
            if not seg.committed:
                seg.committed = True
                committed += seg.token_count
                # 每次只 commit 一段，避免过度丢弃
                break
        self.tracker.committed_tokens += committed

    def _collapse(
        self,
        messages: List[Message],
        tokens_before: int,
    ) -> CompactResult:
        """执行坍缩：移除所有 committed segments"""
        committed_segments = [s for s in self.tracker.segments if s.committed]

        if not committed_segments:
            # 没有 committed 的段，退化为普通截断
            return CompactResult(
                stage=CompactStage.AUTO,
                action=CompactAction.SKIP,
                messages=messages,
                tokens_before=tokens_before,
                tokens_after=tokens_before,
            )

        # 收集要移除的索引
        remove_indices = set()
        for seg in committed_segments:
            for i in range(seg.start_idx, seg.end_idx + 1):
                remove_indices.add(i)

        # 构建结果
        collapsed_notice = Message(
            role=MessageRole.ASSISTANT,
            content=(
                f"[系统] 已坍缩 {len(committed_segments)} 个旧对话段 "
                f"(~{self.tracker.committed_tokens} tokens) 以释放上下文空间。"
            ),
        )

        result_messages = [collapsed_notice]
        for i, msg in enumerate(messages):
            if i not in remove_indices:
                result_messages.append(msg)

        tokens_after = self._counter.count_messages(result_messages)

        self.tracker.collapsed_count += 1
        self.tracker.committed_tokens = 0
        self.tracker.segments = [
            s for s in self.tracker.segments if not s.committed
        ]
        self.tracker.state = CollapseState.IDLE

        logger.info(
            "[Collapse] Collapsed %d segments: %d→%d tokens",
            len(committed_segments),
            tokens_before,
            tokens_after,
        )

        return CompactResult(
            stage=CompactStage.AUTO,
            action=CompactAction.SUMMARIZE,
            messages=result_messages,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
        )

    def reset(self) -> None:
        """重置坍缩状态"""
        self.tracker.reset()
