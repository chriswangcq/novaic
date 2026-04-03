"""
Compact Engine — Pipeline (多阶段压缩管线)

完整编排：TimeBased MC → MicroCompact → SessionMemory → AutoCompact/Collapse → Emergency
含 Post-compact Cleanup 回调。
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .auto import auto_compact, should_auto_compact
from .cleanup import run_post_compact_cleanup
from .collapse import CollapseConfig, CollapseState, ContextCollapse
from .micro import micro_compact
from .protocols import DefaultTokenCounter, NoOpSummarizer, Summarizer, TokenCounter
from .session_memory import (
    SessionMemory,
    compact_session_memory,
    should_compact_session_memory,
)
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

logger = logging.getLogger("compact_engine.pipeline")


class CompactPipeline:
    """
    完整多阶段压缩管线
    
    执行顺序（与 Claude Code 对齐）：
    
    1. TimeBased MC — 距上次消息 >N 分钟时清理旧 tool 输出
    2. MicroCompact — 清理旧 tool 输出（零 API 成本）
    3. Session Memory — 压缩 session memory（如果超限）
    4. AutoCompact / ContextCollapse — 阈值触发的摘要压缩
    5. Emergency — API prompt_too_long 后的紧急压缩
    
    每阶段输出的消息是下一阶段的输入。
    任一阶段将 token 降到安全线以下后，后续阶段跳过。
    压缩完成后执行 Post-compact Cleanup 回调。
    
    Usage:
        pipeline = CompactPipeline(
            config=CompactConfig(context_window=200_000),
            summarizer=my_summarizer,
        )
        tracking = CompactTracking()
        
        result = pipeline.run(messages, tracking)
        if result.action != CompactAction.SKIP:
            messages = result.messages
    """

    def __init__(
        self,
        config: Optional[CompactConfig] = None,
        summarizer: Optional[Summarizer] = None,
        counter: Optional[TokenCounter] = None,
        time_config: Optional[TimeBasedConfig] = None,
        collapse_config: Optional[CollapseConfig] = None,
        session_memory: Optional[SessionMemory] = None,
    ):
        self._config = config or CompactConfig()
        self._summarizer = summarizer or NoOpSummarizer()
        self._counter = counter or DefaultTokenCounter()
        self._time_config = time_config or TimeBasedConfig()
        self._collapse = ContextCollapse(
            collapse_config, self._config, self._counter,
        )
        self._session_memory = session_memory

    @property
    def config(self) -> CompactConfig:
        return self._config

    @config.setter
    def config(self, value: CompactConfig) -> None:
        self._config = value

    @property
    def session_memory(self) -> Optional[SessionMemory]:
        return self._session_memory

    @session_memory.setter
    def session_memory(self, value: Optional[SessionMemory]) -> None:
        self._session_memory = value

    def run(
        self,
        messages: List[Message],
        tracking: CompactTracking,
    ) -> CompactResult:
        """
        执行完整压缩管线。
        """
        tracking.turn_counter += 1
        current = messages
        last_result: Optional[CompactResult] = None

        # ── Stage 1: Time-based MicroCompact ──
        time_result = time_based_micro_compact(
            current, self._config, self._time_config, self._counter,
        )
        if time_result is not None and time_result.action != CompactAction.SKIP:
            current = time_result.messages
            last_result = time_result
            logger.info(
                "[Pipeline] TimeBased MC saved %d tokens",
                time_result.tokens_saved,
            )

        # ── Stage 2: MicroCompact ──
        micro_result = micro_compact(current, self._config, self._counter)
        if micro_result.action != CompactAction.SKIP:
            current = micro_result.messages
            last_result = micro_result
            logger.info(
                "[Pipeline] MicroCompact saved %d tokens",
                micro_result.tokens_saved,
            )

        # ── Stage 3: Session Memory Compact ──
        if self._session_memory and should_compact_session_memory(
            self._session_memory, self._counter,
        ):
            self._session_memory = compact_session_memory(
                self._session_memory, self._summarizer, self._counter,
            )
            logger.info(
                "[Pipeline] SessionMemory compacted to %d tokens",
                self._session_memory.total_tokens,
            )

        # ── Stage 4: AutoCompact 或 ContextCollapse ──
        if self._collapse.enabled:
            # 使用 ContextCollapse（更精细）
            state, collapse_result = self._collapse.evaluate(current)
            if collapse_result and collapse_result.action != CompactAction.SKIP:
                current = collapse_result.messages
                last_result = collapse_result
                tracking.compacted = True
                tracking.compact_count += 1
                tracking.total_tokens_saved += collapse_result.tokens_saved
                logger.info(
                    "[Pipeline] ContextCollapse saved %d tokens (state=%s)",
                    collapse_result.tokens_saved,
                    state.value,
                )
        elif should_auto_compact(current, self._config, tracking, self._counter):
            # 使用 AutoCompact
            auto_result = auto_compact(
                current, self._config, tracking,
                self._summarizer, self._counter,
            )
            if auto_result.action != CompactAction.SKIP:
                current = auto_result.messages
                last_result = auto_result
                logger.info(
                    "[Pipeline] AutoCompact saved %d tokens",
                    auto_result.tokens_saved,
                )

        # ── Post-compact cleanup ──
        if last_result and last_result.action != CompactAction.SKIP:
            run_post_compact_cleanup(last_result)

        if last_result is None:
            return CompactResult(
                stage=CompactStage.MICRO,
                action=CompactAction.SKIP,
                messages=messages,
                tokens_before=self._counter.count_messages(messages),
                tokens_after=self._counter.count_messages(messages),
            )

        return last_result

    def emergency_compact(
        self,
        messages: List[Message],
        tracking: CompactTracking,
    ) -> CompactResult:
        """
        紧急压缩 — 当 API 返回 prompt_too_long 时调用。
        """
        tokens_before = self._counter.count_messages(messages)
        logger.warning(
            "[Pipeline] Emergency compact triggered: %d tokens", tokens_before,
        )

        # 1. 先尝试 session memory compact
        if self._session_memory and should_compact_session_memory(
            self._session_memory, self._counter,
        ):
            self._session_memory = compact_session_memory(
                self._session_memory, self._summarizer, self._counter,
            )

        # 2. 尝试 auto_compact（临时禁用熔断器）
        saved_failures = tracking.consecutive_failures
        tracking.consecutive_failures = 0

        result = auto_compact(
            messages, self._config, tracking,
            self._summarizer, self._counter,
        )

        if result.success and result.action != CompactAction.SKIP:
            run_post_compact_cleanup(result)
            return CompactResult(
                stage=CompactStage.REACTIVE,
                action=result.action,
                messages=result.messages,
                tokens_before=tokens_before,
                tokens_after=result.tokens_after,
                summary=result.summary,
            )

        # 3. Auto compact 失败 → 暴力截断
        logger.warning("[Pipeline] Emergency: falling back to truncation")
        tracking.consecutive_failures = saved_failures + 1

        truncated = self._truncate_messages(messages)
        tokens_after = self._counter.count_messages(truncated)

        truncation_result = CompactResult(
            stage=CompactStage.REACTIVE,
            action=CompactAction.EMERGENCY,
            messages=truncated,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            error="Emergency truncation (summarizer failed)",
        )
        run_post_compact_cleanup(truncation_result)
        return truncation_result

    def _truncate_messages(self, messages: List[Message]) -> List[Message]:
        """暴力截断：保留系统消息 + 最近 20% 的消息"""
        system_msgs = [m for m in messages if m.role == MessageRole.SYSTEM]
        non_system = [m for m in messages if m.role != MessageRole.SYSTEM]

        keep_count = max(5, len(non_system) // 5)
        recent = non_system[-keep_count:]

        truncation_notice = Message(
            role=MessageRole.ASSISTANT,
            content=(
                f"[系统] 由于上下文超限，历史消息已被截断。"
                f"保留了最近 {keep_count} 条消息。"
            ),
        )

        return system_msgs + [truncation_notice] + recent

    # ── 诊断 ──

    def get_token_status(self, messages: List[Message]) -> dict:
        """返回当前 token 使用状态"""
        token_count = self._counter.count_messages(messages)
        effective = self._config.effective_window
        auto_threshold = self._config.auto_threshold

        return {
            "token_count": token_count,
            "effective_window": effective,
            "auto_threshold": auto_threshold,
            "percent_used": round(token_count / effective * 100, 1) if effective else 0,
            "tokens_until_compact": max(0, auto_threshold - token_count),
            "should_compact": token_count >= auto_threshold,
            "collapse_enabled": self._collapse.enabled,
            "collapse_state": self._collapse.tracker.state.value if self._collapse.enabled else None,
            "session_memory_tokens": self._session_memory.total_tokens if self._session_memory else 0,
        }
