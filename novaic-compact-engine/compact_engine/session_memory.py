"""
Compact Engine — Session Memory Compact

借鉴 Claude Code sessionMemoryCompact.ts:
将 session memory（会话记忆文件）作为独立压缩目标。
当 session memory 占用过多 token 时，优先压缩它。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .protocols import DefaultTokenCounter, Summarizer, TokenCounter

logger = logging.getLogger("compact_engine.session_memory")


# Session memory token 上限
MAX_SESSION_MEMORY_TOKENS = 12_000
MAX_SECTION_LENGTH = 3_000


@dataclass
class SessionMemory:
    """
    会话记忆 — 跨轮对话持久化的结构化上下文
    
    Sections:
    - current_state: 当前工作状态
    - decisions: 关键技术决策
    - errors: 错误与修正记录
    - todo: 待办事项
    """
    sections: Dict[str, str] = field(default_factory=dict)
    total_tokens: int = 0

    def set_section(self, key: str, content: str, counter: Optional[TokenCounter] = None) -> None:
        _counter = counter or DefaultTokenCounter()
        self.sections[key] = content
        self._recalculate_tokens(_counter)

    def get_section(self, key: str) -> str:
        return self.sections.get(key, "")

    def to_text(self) -> str:
        """序列化为文本（注入 system prompt 或保存到文件）"""
        parts = []
        for key, content in self.sections.items():
            parts.append(f"## {key}\n{content}")
        return "\n\n".join(parts)

    @classmethod
    def from_text(cls, text: str, counter: Optional[TokenCounter] = None) -> "SessionMemory":
        """从文本反序列化"""
        _counter = counter or DefaultTokenCounter()
        mem = cls()
        current_key = ""
        current_lines: List[str] = []

        for line in text.split("\n"):
            if line.startswith("## "):
                if current_key:
                    mem.sections[current_key] = "\n".join(current_lines)
                current_key = line[3:].strip()
                current_lines = []
            else:
                current_lines.append(line)

        if current_key:
            mem.sections[current_key] = "\n".join(current_lines)

        mem._recalculate_tokens(_counter)
        return mem

    def _recalculate_tokens(self, counter: TokenCounter) -> None:
        self.total_tokens = counter.count(self.to_text())


def should_compact_session_memory(
    memory: SessionMemory,
    counter: Optional[TokenCounter] = None,
) -> bool:
    """判断 session memory 是否需要压缩"""
    _counter = counter or DefaultTokenCounter()
    return memory.total_tokens > MAX_SESSION_MEMORY_TOKENS


def compact_session_memory(
    memory: SessionMemory,
    summarizer: Summarizer,
    counter: Optional[TokenCounter] = None,
) -> SessionMemory:
    """
    压缩 session memory。
    
    策略：
    1. 找到超长的 sections
    2. 使用 Summarizer 压缩它们
    3. 始终保留 current_state 的完整性
    
    Returns:
        压缩后的新 SessionMemory
    """
    _counter = counter or DefaultTokenCounter()

    if not should_compact_session_memory(memory, _counter):
        return memory

    from .types import Message, MessageRole

    new_sections = {}
    budget_remaining = MAX_SESSION_MEMORY_TOKENS

    # 按重要性排序：current_state > errors > todo > 其余
    priority_order = ["current_state", "errors", "todo"]
    sorted_keys = []
    for key in priority_order:
        if key in memory.sections:
            sorted_keys.append(key)
    for key in memory.sections:
        if key not in sorted_keys:
            sorted_keys.append(key)

    for key in sorted_keys:
        content = memory.sections[key]
        section_tokens = _counter.count(content)

        if section_tokens <= MAX_SECTION_LENGTH and budget_remaining >= section_tokens:
            new_sections[key] = content
            budget_remaining -= section_tokens
        elif budget_remaining > 500:  # 至少留 500 tokens 给摘要
            # 需要压缩
            target_tokens = min(MAX_SECTION_LENGTH, budget_remaining - 200)
            try:
                msgs = [Message(
                    role=MessageRole.USER,
                    content=content,
                )]
                summary = summarizer.summarize(
                    msgs,
                    max_tokens=target_tokens,
                    instructions=(
                        f"压缩以下 '{key}' 部分内容，保留最关键的信息。"
                        f"目标长度约 {target_tokens} tokens。"
                    ),
                )
                new_sections[key] = summary
                budget_remaining -= _counter.count(summary)
            except Exception as e:
                logger.error(
                    "[SessionMemory] Failed to compact section '%s': %s",
                    key, e,
                )
                # 截断作为兜底
                truncated = content[:target_tokens * 4]  # 粗估 4 chars/token
                new_sections[key] = truncated + "\n[...已截断]"
                budget_remaining -= _counter.count(new_sections[key])

    result = SessionMemory(sections=new_sections)
    result._recalculate_tokens(_counter)

    logger.info(
        "[SessionMemory] Compacted: %d → %d tokens (%d sections)",
        memory.total_tokens,
        result.total_tokens,
        len(result.sections),
    )

    return result
