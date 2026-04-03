"""
Compact Engine — Protocols (接口协议)

集成方需实现的外部依赖接口。
引擎本身不调用 LLM，而是通过 Summarizer 协议将调用权交还给集成方。
"""

from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from .types import Message


@runtime_checkable
class TokenCounter(Protocol):
    """
    Token 计数协议
    
    集成方可提供精确的 tokenizer 实现，
    引擎提供默认的粗估实现。
    """

    def count(self, text: str) -> int:
        """计算文本的 token 数"""
        ...

    def count_messages(self, messages: List[Message]) -> int:
        """计算消息列表的总 token 数"""
        ...


@runtime_checkable
class Summarizer(Protocol):
    """
    摘要生成协议 — 将 LLM 调用权交还给集成方
    
    集成方实现此接口，使用自己的 LLM client 生成摘要。
    引擎不直接调用任何 LLM API。
    
    NovAIC 集成示例:
        class NovAICSummarizer:
            def __init__(self, llm_client):
                self._client = llm_client
            
            def summarize(self, messages, max_tokens):
                prompt = self._build_summary_prompt(messages)
                return self._client.complete(prompt, max_tokens=max_tokens)
    """

    def summarize(
        self,
        messages: List[Message],
        max_tokens: int = 20_000,
        instructions: str = "",
    ) -> str:
        """
        将消息列表压缩为摘要文本。
        
        Args:
            messages: 要压缩的消息列表
            max_tokens: 摘要最大 token 数
            instructions: 额外的压缩指令
            
        Returns:
            摘要文本
        """
        ...


# ── 默认实现 ──

class DefaultTokenCounter:
    """默认 token 计数器：字符数 / 4"""

    def count(self, text: str) -> int:
        return max(1, len(text) // 4)

    def count_messages(self, messages: List[Message]) -> int:
        total = 0
        for msg in messages:
            if msg.token_count > 0:
                total += msg.token_count
            else:
                total += self.count(msg.content)
        return total


class NoOpSummarizer:
    """
    无操作摘要器 — 用于测试和降级场景。
    直接拼接保留消息的内容。
    """

    def summarize(
        self,
        messages: List[Message],
        max_tokens: int = 20_000,
        instructions: str = "",
    ) -> str:
        # 保留最后 N 条消息的关键内容
        parts = ["[会话摘要 - 自动生成]", ""]
        for msg in messages[-10:]:
            role = msg.role.value
            content = msg.content[:500]
            parts.append(f"[{role}] {content}")
        return "\n".join(parts)
