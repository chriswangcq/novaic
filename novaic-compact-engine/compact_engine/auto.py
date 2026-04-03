"""
Compact Engine — AutoCompact (自动摘要压缩)

借鉴 Claude Code autoCompact.ts:
当 token 用量接近上下文窗口时自动触发，
将历史消息压缩为结构化摘要。
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .protocols import DefaultTokenCounter, NoOpSummarizer, Summarizer, TokenCounter
from .types import (
    CompactAction,
    CompactConfig,
    CompactResult,
    CompactStage,
    CompactTracking,
    Message,
    MessageRole,
)

logger = logging.getLogger("compact_engine.auto")

# 摘要前缀（注入到压缩后的消息中）
SUMMARY_PREFIX = "[系统] 以下是对话历史的压缩摘要："


def should_auto_compact(
    messages: List[Message],
    config: CompactConfig,
    tracking: CompactTracking,
    counter: Optional[TokenCounter] = None,
) -> bool:
    """
    判断是否需要触发 AutoCompact。
    
    规则：
    1. 当前 token 用量 >= auto_threshold
    2. 未触发熔断器（连续失败 < max_consecutive_failures）
    3. 消息列表中有足够内容可压缩
    """
    if tracking.consecutive_failures >= config.max_consecutive_failures:
        logger.debug(
            "[AutoCompact] Circuit breaker active (%d consecutive failures)",
            tracking.consecutive_failures,
        )
        return False

    _counter = counter or DefaultTokenCounter()
    token_count = _counter.count_messages(messages)

    logger.debug(
        "[AutoCompact] tokens=%d threshold=%d effective_window=%d",
        token_count,
        config.auto_threshold,
        config.effective_window,
    )

    return token_count >= config.auto_threshold


def auto_compact(
    messages: List[Message],
    config: CompactConfig,
    tracking: CompactTracking,
    summarizer: Optional[Summarizer] = None,
    counter: Optional[TokenCounter] = None,
) -> CompactResult:
    """
    执行 AutoCompact — 将旧消息压缩为摘要。
    
    流程：
    1. 检查是否需要压缩
    2. 将消息分为"可压缩部分"和"保留部分"
    3. 使用 Summarizer 协议生成摘要
    4. 用摘要 message 替换被压缩的消息
    5. 更新 tracking 状态
    
    关键设计：
    - Summarizer 是协议接口，引擎不直接调 LLM
    - 保留最近的消息不被压缩（保持上下文连贯性）
    - 熔断器：连续 N 次失败后停止重试
    """
    _counter = counter or DefaultTokenCounter()
    _summarizer = summarizer or NoOpSummarizer()
    tokens_before = _counter.count_messages(messages)

    if not should_auto_compact(messages, config, tracking, _counter):
        return CompactResult(
            stage=CompactStage.AUTO,
            action=CompactAction.SKIP,
            messages=messages,
            tokens_before=tokens_before,
            tokens_after=tokens_before,
        )

    # 分割：保留最近的消息，压缩较旧的
    split_idx = _find_compact_split(messages, config, _counter)

    if split_idx <= 1:
        # 没有足够的旧消息可压缩
        return CompactResult(
            stage=CompactStage.AUTO,
            action=CompactAction.SKIP,
            messages=messages,
            tokens_before=tokens_before,
            tokens_after=tokens_before,
        )

    old_messages = messages[:split_idx]
    recent_messages = messages[split_idx:]

    logger.info(
        "[AutoCompact] Compacting %d messages (keeping %d recent)",
        len(old_messages),
        len(recent_messages),
    )

    # 调用 Summarizer 协议
    try:
        summary = _summarizer.summarize(
            old_messages,
            max_tokens=config.auto_max_summary_tokens,
            instructions=(
                "请将以上对话历史压缩为结构化摘要。保留：\n"
                "1. 当前正在进行的任务状态\n"
                "2. 关键的技术决策和原因\n"
                "3. 重要的文件修改记录\n"
                "4. 未完成的待办事项\n"
                "删除：重复的工具输出、探索性的失败尝试、冗余的讨论。"
            ),
        )
    except Exception as e:
        logger.error("[AutoCompact] Summarizer failed: %s", e)
        tracking.consecutive_failures += 1
        return CompactResult(
            stage=CompactStage.AUTO,
            action=CompactAction.SUMMARIZE,
            messages=messages,
            tokens_before=tokens_before,
            tokens_after=tokens_before,
            error=str(e),
        )

    # 构建压缩后的消息列表
    summary_message = Message(
        role=MessageRole.ASSISTANT,
        content=f"{SUMMARY_PREFIX}\n\n{summary}",
        token_count=_counter.count(summary),
    )

    result_messages = [summary_message] + recent_messages
    tokens_after = _counter.count_messages(result_messages)

    # 更新 tracking
    tracking.compacted = True
    tracking.consecutive_failures = 0  # 成功，重置熔断器
    tracking.total_tokens_saved += tokens_before - tokens_after
    tracking.compact_count += 1
    tracking.turn_counter = 0

    logger.info(
        "[AutoCompact] Done: %d→%d tokens (saved %d), %d→%d messages",
        tokens_before,
        tokens_after,
        tokens_before - tokens_after,
        len(messages),
        len(result_messages),
    )

    return CompactResult(
        stage=CompactStage.AUTO,
        action=CompactAction.SUMMARIZE,
        messages=result_messages,
        tokens_before=tokens_before,
        tokens_after=tokens_after,
        summary=summary,
    )


def _find_compact_split(
    messages: List[Message],
    config: CompactConfig,
    counter: TokenCounter,
) -> int:
    """
    找到压缩分割点：从最后向前累计 token，
    保留至少 auto_buffer_tokens 的最近消息。
    """
    target_keep = config.auto_buffer_tokens
    accumulated = 0

    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        tokens = msg.token_count or counter.count(msg.content)
        accumulated += tokens
        if accumulated >= target_keep:
            return i

    return 0  # 全部保留
