"""
Compact Engine — MicroCompact (工具输出清理)

借鉴 Claude Code microCompact.ts:
清理旧的 tool_result 内容，保留最近 N 个。
零 API 成本，纯本地操作。
"""

from __future__ import annotations

import logging
from typing import List, Optional, Set

from .protocols import DefaultTokenCounter, TokenCounter
from .types import (
    CompactAction,
    CompactConfig,
    CompactResult,
    CompactStage,
    Message,
    MessageRole,
)

logger = logging.getLogger("compact_engine.micro")

# 被清理的 tool output 替换为此标记
CLEARED_MARKER = "[旧工具输出已清理]"


def micro_compact(
    messages: List[Message],
    config: CompactConfig,
    counter: Optional[TokenCounter] = None,
) -> CompactResult:
    """
    MicroCompact — 清理旧 tool 输出
    
    策略：
    1. 找出所有可压缩的 tool_result
    2. 保留最近 keep_recent 个
    3. 将其余的 content 替换为 CLEARED_MARKER
    4. 跳过 token 数低于阈值的小输出
    
    返回 CompactResult（即使无操作也返回 SKIP）。
    """
    _counter = counter or DefaultTokenCounter()
    tokens_before = _counter.count_messages(messages)

    # 收集可压缩的 tool output（按出现顺序）
    compactable_indices = []
    compactable_tools = set(config.micro_compactable_tools)

    for i, msg in enumerate(messages):
        if not msg.is_tool_output:
            continue
        if msg.tool_name and msg.tool_name not in compactable_tools:
            continue
        if msg.content == CLEARED_MARKER:
            continue  # 已清理
        token_count = msg.token_count or _counter.count(msg.content)
        if token_count < config.micro_min_tool_tokens:
            continue  # 太小，不值得清理
        compactable_indices.append(i)

    if not compactable_indices:
        return CompactResult(
            stage=CompactStage.MICRO,
            action=CompactAction.SKIP,
            messages=messages,
            tokens_before=tokens_before,
            tokens_after=tokens_before,
        )

    # 保留最近 N 个
    keep_count = max(1, config.micro_keep_recent)
    if len(compactable_indices) <= keep_count:
        return CompactResult(
            stage=CompactStage.MICRO,
            action=CompactAction.SKIP,
            messages=messages,
            tokens_before=tokens_before,
            tokens_after=tokens_before,
        )

    # 需要清理的索引
    to_clear = compactable_indices[:-keep_count]
    keep_set = set(compactable_indices[-keep_count:])

    # 执行清理（不修改原列表，返回新列表）
    result_messages = []
    pruned_ids = []

    for i, msg in enumerate(messages):
        if i in to_clear:
            # 替换内容
            cleared = Message(
                role=msg.role,
                content=CLEARED_MARKER,
                token_count=_counter.count(CLEARED_MARKER),
                tool_name=msg.tool_name,
                tool_id=msg.tool_id,
                timestamp=msg.timestamp,
                metadata=msg.metadata,
            )
            result_messages.append(cleared)
            if msg.tool_id:
                pruned_ids.append(msg.tool_id)
        else:
            result_messages.append(msg)

    tokens_after = _counter.count_messages(result_messages)

    logger.info(
        "[MicroCompact] Cleared %d/%d tool outputs, saved ~%d tokens",
        len(to_clear),
        len(compactable_indices),
        tokens_before - tokens_after,
    )

    return CompactResult(
        stage=CompactStage.MICRO,
        action=CompactAction.PRUNE_TOOL_OUTPUTS,
        messages=result_messages,
        tokens_before=tokens_before,
        tokens_after=tokens_after,
        pruned_tool_ids=pruned_ids,
    )
