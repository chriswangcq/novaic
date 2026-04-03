"""
Compact Engine — Skill-Scoped Compaction (技能域压缩)

NovAIC 原创设计 —— 将 skill 执行当作事务单元：
- PRE_INVOKE:  checkpoint 当前 context → context_start
- 执行:        skill prompt 注入 → LLM tools 执行 → 生成大量中间消息
- POST_INVOKE: summarize(delta) → skill_result
- 最终:        context = context_start + skill_result

Claude Code 没有此功能。它只有时间/阈值触发的盲压缩，
不理解"这段操作是一个完整语义单元，可以安全折叠为结果"。

类比：
- 函数调用 → 栈帧回收（只保留返回值）
- 数据库事务 → 只保留 commit 结果
- Git squash → 合并 50 个中间 commit 为 1 个结果 commit
"""

from __future__ import annotations

import copy
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from .protocols import DefaultTokenCounter, Summarizer, TokenCounter
from .types import (
    CompactAction,
    CompactConfig,
    CompactResult,
    CompactStage,
    Message,
    MessageRole,
)

logger = logging.getLogger("compact_engine.skill_scoped")


class SkillPhase(str, Enum):
    """技能执行阶段"""
    IDLE = "idle"           # 未在执行 skill
    RUNNING = "running"     # skill 正在执行
    COMPLETED = "completed" # skill 已完成，待压缩


@dataclass
class SkillCheckpoint:
    """
    技能执行的上下文快照
    
    保存 skill 调用前的 context 状态，
    执行完成后用于计算 delta 并压缩。
    """
    skill_id: str
    skill_name: str
    context_start: List[Message]          # checkpoint 时刻的消息快照
    start_index: int                       # skill prompt 注入位置
    start_time: float = 0.0
    start_tokens: int = 0                  # checkpoint 时的 token 数
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class SkillScopedTracker:
    """技能域压缩追踪器"""
    phase: SkillPhase = SkillPhase.IDLE
    current_checkpoint: Optional[SkillCheckpoint] = None
    history: List[Dict] = field(default_factory=list)  # 压缩历史
    total_tokens_saved: int = 0
    total_skills_compacted: int = 0


class SkillScopedCompactor:
    """
    技能域压缩器
    
    Usage:
        compactor = SkillScopedCompactor(summarizer=my_summarizer)
        
        # 1. Skill 调用前: checkpoint
        compactor.checkpoint(messages, skill_id="deploy", skill_name="Deploy")
        
        # 2. Skill 执行中: LLM 通过 tools 执行任务...
        #    messages 列表不断增长
        
        # 3. Skill 完成后: compact
        result = compactor.compact(messages)
        if result:
            messages = result.messages   # context_start + skill_result
    
    嵌套安全:
        不支持嵌套 skill（调用 skill 中再调另一个 skill）。
        如果已有 checkpoint，新的 checkpoint 会覆盖旧的。
    """

    def __init__(
        self,
        summarizer: Optional[Summarizer] = None,
        counter: Optional[TokenCounter] = None,
        config: Optional[CompactConfig] = None,
        min_delta_messages: int = 5,
        min_delta_tokens: int = 500,
    ):
        self._summarizer = summarizer
        self._counter = counter or DefaultTokenCounter()
        self._config = config or CompactConfig()
        self._min_delta_messages = min_delta_messages  # delta 少于此值不压缩
        self._min_delta_tokens = min_delta_tokens      # delta token 少于此值不压缩
        self.tracker = SkillScopedTracker()

    # ── PRE_INVOKE: Checkpoint ──

    def checkpoint(
        self,
        messages: List[Message],
        skill_id: str,
        skill_name: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> SkillCheckpoint:
        """
        PRE_INVOKE: 保存当前 context 快照。
        
        此时 skill prompt 还未注入 messages。
        """
        if self.tracker.phase == SkillPhase.RUNNING:
            logger.warning(
                "[SkillScoped] Overwriting existing checkpoint for '%s'",
                self.tracker.current_checkpoint.skill_name
                if self.tracker.current_checkpoint else "unknown",
            )

        checkpoint = SkillCheckpoint(
            skill_id=skill_id,
            skill_name=skill_name,
            context_start=copy.copy(messages),  # shallow copy 足够
            start_index=len(messages),
            start_time=time.time(),
            start_tokens=self._counter.count_messages(messages),
            metadata=metadata or {},
        )

        self.tracker.phase = SkillPhase.RUNNING
        self.tracker.current_checkpoint = checkpoint

        logger.info(
            "[SkillScoped] Checkpoint created: skill='%s', "
            "start_index=%d, start_tokens=%d",
            skill_name,
            checkpoint.start_index,
            checkpoint.start_tokens,
        )

        return checkpoint

    # ── POST_INVOKE: Compact ──

    def compact(
        self,
        messages: List[Message],
        extra_instructions: str = "",
    ) -> Optional[CompactResult]:
        """
        POST_INVOKE: 将 skill 执行期间的 delta 压缩为 skill_result。
        
        最终 context = context_start + skill_result_message
        
        Args:
            messages: 当前完整消息列表（含 skill 执行期间新增的所有消息）
            extra_instructions: 额外的摘要指令
        
        Returns:
            CompactResult（成功）或 None（不需要压缩）
        """
        if self.tracker.phase != SkillPhase.RUNNING:
            logger.warning("[SkillScoped] No active checkpoint to compact")
            return None

        cp = self.tracker.current_checkpoint
        if not cp:
            return None

        # 计算 delta
        start_idx = cp.start_index
        delta_messages = messages[start_idx:]
        delta_count = len(delta_messages)
        delta_tokens = self._counter.count_messages(delta_messages)

        logger.info(
            "[SkillScoped] Skill '%s' delta: %d messages, ~%d tokens",
            cp.skill_name,
            delta_count,
            delta_tokens,
        )

        # 判断是否值得压缩
        if delta_count < self._min_delta_messages:
            logger.info(
                "[SkillScoped] Delta too small (%d < %d messages), skip",
                delta_count,
                self._min_delta_messages,
            )
            self._finalize(False)
            return None

        if delta_tokens < self._min_delta_tokens:
            logger.info(
                "[SkillScoped] Delta tokens too small (%d < %d), skip",
                delta_tokens,
                self._min_delta_tokens,
            )
            self._finalize(False)
            return None

        # 提取 delta 中的关键信息辅助摘要
        skill_result = self._summarize_delta(
            cp.skill_name,
            delta_messages,
            extra_instructions,
        )

        # 构建压缩后的 context: context_start + skill_result
        elapsed = time.time() - cp.start_time
        result_message = Message(
            role=MessageRole.ASSISTANT,
            content=(
                f"[Skill Result: {cp.skill_name}]\n"
                f"执行时长: {elapsed:.1f}s | "
                f"原始交互: {delta_count} 条消息\n\n"
                f"{skill_result}"
            ),
            token_count=self._counter.count(skill_result),
            metadata={
                "skill_scoped": "true",
                "skill_id": cp.skill_id,
                "skill_name": cp.skill_name,
                "delta_messages": str(delta_count),
                "delta_tokens": str(delta_tokens),
                "elapsed_seconds": f"{elapsed:.1f}",
            },
        )

        # context_start + skill_result
        compacted_messages = list(cp.context_start) + [result_message]

        tokens_before = self._counter.count_messages(messages)
        tokens_after = self._counter.count_messages(compacted_messages)

        # 更新追踪
        self.tracker.total_tokens_saved += tokens_before - tokens_after
        self.tracker.total_skills_compacted += 1
        self.tracker.history.append({
            "skill_id": cp.skill_id,
            "skill_name": cp.skill_name,
            "delta_messages": delta_count,
            "delta_tokens": delta_tokens,
            "result_tokens": result_message.token_count,
            "tokens_saved": tokens_before - tokens_after,
            "elapsed": round(elapsed, 1),
        })

        self._finalize(True)

        logger.info(
            "[SkillScoped] Compacted '%s': %d msgs → 1 result, "
            "%d → %d tokens (saved %d)",
            cp.skill_name,
            delta_count,
            tokens_before,
            tokens_after,
            tokens_before - tokens_after,
        )

        return CompactResult(
            stage=CompactStage.AUTO,
            action=CompactAction.SUMMARIZE,
            messages=compacted_messages,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            summary=skill_result,
        )

    # ── 内部方法 ──

    def _summarize_delta(
        self,
        skill_name: str,
        delta: List[Message],
        extra_instructions: str,
    ) -> str:
        """
        将 skill delta 压缩为结果摘要。
        
        优先使用 Summarizer 协议。
        如果没有 Summarizer，则使用规则提取兜底。
        """
        if self._summarizer:
            try:
                return self._summarizer.summarize(
                    delta,
                    max_tokens=min(2000, self._config.auto_max_summary_tokens),
                    instructions=(
                        f"将以下技能 '{skill_name}' 的执行过程压缩为结果摘要。\n"
                        f"保留：\n"
                        f"1. 最终执行结果（成功/失败）\n"
                        f"2. 修改了哪些文件（列出路径和变更类型）\n"
                        f"3. 关键命令的输出\n"
                        f"4. 错误信息（如果有）\n"
                        f"5. 需要后续注意的事项\n\n"
                        f"删除：中间的探索、重复的输出、工具调用细节。\n"
                        f"{extra_instructions}"
                    ),
                )
            except Exception as e:
                logger.error(
                    "[SkillScoped] Summarizer failed, falling back to extraction: %s",
                    e,
                )

        # Fallback: 规则提取
        return self._extract_key_results(skill_name, delta)

    def _extract_key_results(
        self,
        skill_name: str,
        delta: List[Message],
    ) -> str:
        """
        兜底方案：从 delta 中提取关键信息（不需要 LLM）。
        
        策略：
        - 保留最后一条 assistant 消息（通常是最终回答）
        - 提取 tool 调用的文件路径
        - 保留错误信息
        """
        last_assistant = ""
        files_modified = set()
        errors = []

        for msg in delta:
            if msg.role == MessageRole.ASSISTANT:
                last_assistant = msg.content

            if msg.is_tool_output and msg.tool_name:
                # 提取文件路径（简单启发式）
                for line in msg.content.split("\n")[:5]:
                    if "/" in line and ("." in line.split("/")[-1]):
                        path = line.strip().split()[-1] if line.strip() else ""
                        if path and len(path) < 200:
                            files_modified.add(path)

                # 提取错误
                for line in msg.content.split("\n"):
                    lower = line.lower()
                    if any(kw in lower for kw in ["error", "failed", "exception"]):
                        errors.append(line.strip()[:200])

        parts = [f"技能 '{skill_name}' 执行完成。"]

        if files_modified:
            parts.append(f"\n修改的文件: {', '.join(list(files_modified)[:10])}")

        if errors:
            parts.append(f"\n错误/警告:")
            for e in errors[:5]:
                parts.append(f"  - {e}")

        if last_assistant:
            # 保留最终回答的前 500 字符
            truncated = last_assistant[:500]
            if len(last_assistant) > 500:
                truncated += "..."
            parts.append(f"\n最终回答:\n{truncated}")

        return "\n".join(parts)

    def _finalize(self, compacted: bool) -> None:
        """重置状态"""
        self.tracker.phase = SkillPhase.COMPLETED if compacted else SkillPhase.IDLE
        self.tracker.current_checkpoint = None
        # 短暂设为 COMPLETED 后立即回到 IDLE
        self.tracker.phase = SkillPhase.IDLE

    # ── 查询 ──

    def is_running(self) -> bool:
        return self.tracker.phase == SkillPhase.RUNNING

    def cancel(self) -> None:
        """取消当前 checkpoint（skill 被中断时调用）"""
        if self.tracker.phase == SkillPhase.RUNNING:
            logger.info("[SkillScoped] Checkpoint cancelled")
        self._finalize(False)

    def get_stats(self) -> dict:
        return {
            "phase": self.tracker.phase.value,
            "total_skills_compacted": self.tracker.total_skills_compacted,
            "total_tokens_saved": self.tracker.total_tokens_saved,
            "history": self.tracker.history[-10:],  # 最近 10 次
        }
