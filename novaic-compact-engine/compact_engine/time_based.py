"""
Compact Engine — Time-based MicroCompact

借鉴 Claude Code maybeTimeBasedMicrocompact():
当距上次 assistant 消息超过 N 分钟时，缓存已过期，
趁此机会清理旧 tool 输出以缩减重写成本。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import List, Optional

from .micro import CLEARED_MARKER
from .protocols import DefaultTokenCounter, TokenCounter
from .types import (
    CompactAction,
    CompactConfig,
    CompactResult,
    CompactStage,
    Message,
    MessageRole,
)

logger = logging.getLogger("compact_engine.time_based")


@dataclass
class TimeBasedConfig:
    """时间触发配置"""
    enabled: bool = True
    gap_threshold_minutes: float = 5.0    # 间隔超过此值触发
    keep_recent: int = 3                  # 保留最近 N 个 tool 输出


def evaluate_time_trigger(
    messages: List[Message],
    config: TimeBasedConfig,
) -> Optional[float]:
    """
    判断是否触发 time-based 清理。
    
    Returns:
        间隔分钟数（触发时），None（不触发）。
    """
    if not config.enabled:
        return None

    # 查找最后一条 assistant 消息
    last_assistant = None
    for msg in reversed(messages):
        if msg.role == MessageRole.ASSISTANT:
            last_assistant = msg
            break

    if not last_assistant or last_assistant.timestamp <= 0:
        return None

    gap_minutes = (time.time() - last_assistant.timestamp) / 60.0

    if gap_minutes < config.gap_threshold_minutes:
        return None

    return gap_minutes


def time_based_micro_compact(
    messages: List[Message],
    compact_config: CompactConfig,
    time_config: Optional[TimeBasedConfig] = None,
    counter: Optional[TokenCounter] = None,
) -> Optional[CompactResult]:
    """
    时间触发的 MicroCompact。
    
    与常规 MicroCompact 的区别：
    - 由时间间隔触发（而非 token 阈值）
    - 利用缓存冷启动时机，更激进地清理
    - 返回 None 表示不触发（由 pipeline 继续下一阶段）
    """
    _config = time_config or TimeBasedConfig()
    _counter = counter or DefaultTokenCounter()

    gap = evaluate_time_trigger(messages, _config)
    if gap is None:
        return None

    # 收集可清理的 tool 输出
    compactable_tools = set(compact_config.micro_compactable_tools)
    tool_indices = []

    for i, msg in enumerate(messages):
        if not msg.is_tool_output:
            continue
        if msg.tool_name and msg.tool_name not in compactable_tools:
            continue
        if msg.content == CLEARED_MARKER:
            continue
        tool_indices.append(i)

    keep_count = max(1, _config.keep_recent)
    if len(tool_indices) <= keep_count:
        return None

    to_clear = set(tool_indices[:-keep_count])
    tokens_before = _counter.count_messages(messages)
    tokens_saved = 0

    result_messages = []
    for i, msg in enumerate(messages):
        if i in to_clear:
            saved = msg.token_count or _counter.count(msg.content)
            tokens_saved += saved - _counter.count(CLEARED_MARKER)
            result_messages.append(Message(
                role=msg.role,
                content=CLEARED_MARKER,
                token_count=_counter.count(CLEARED_MARKER),
                tool_name=msg.tool_name,
                tool_id=msg.tool_id,
                timestamp=msg.timestamp,
                metadata=msg.metadata,
            ))
        else:
            result_messages.append(msg)

    if tokens_saved <= 0:
        return None

    tokens_after = tokens_before - tokens_saved

    logger.info(
        "[TimeBased MC] gap=%.1fmin > %.1fmin threshold, "
        "cleared %d tool results (~%d tokens saved)",
        gap,
        _config.gap_threshold_minutes,
        len(to_clear),
        tokens_saved,
    )

    return CompactResult(
        stage=CompactStage.MICRO,
        action=CompactAction.PRUNE_TOOL_OUTPUTS,
        messages=result_messages,
        tokens_before=tokens_before,
        tokens_after=tokens_after,
        pruned_tool_ids=[
            messages[i].tool_id for i in to_clear
            if messages[i].tool_id
        ],
    )
