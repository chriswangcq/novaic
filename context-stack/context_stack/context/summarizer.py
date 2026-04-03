"""
Context Stack — Structured Summarizer

Generates structured scope summaries.
Phase ⑤ of the lifecycle.
"""
from __future__ import annotations

import logging
import re
from typing import Dict, List

from .types import Message, MessageRole, ScopeRecord

logger = logging.getLogger("context_stack.summarizer")


class StructuredSummarizer:
    """
    Generates a structured summary of a scope's execution.
    
    Uses LLM if available, with rule-based fallback.
    Also extracts metadata (files, tools, errors) via regex.
    """

    def __init__(self, summarizer, counter, max_tokens: int = 20_000):
        self._summarizer = summarizer
        self._counter = counter
        self._max_tokens = max_tokens

    def summarize(
        self,
        scope: ScopeRecord,
        messages: List[Message],
    ) -> str:
        """Full summarization: extract metadata + generate summary text."""
        self._extract_metadata(scope, messages)
        return self._generate_summary(scope, messages)

    # ─────────────────────────────────────────
    # Metadata Extraction (rule-based, zero LLM)
    # ─────────────────────────────────────────

    def _extract_metadata(self, scope: ScopeRecord, messages: List[Message]) -> None:
        files_set = set()
        errors = []
        tools: Dict[str, int] = {}
        decisions = []

        for msg in messages:
            if msg.tool_name:
                tools[msg.tool_name] = tools.get(msg.tool_name, 0) + 1

            content = msg.content or ""

            # File paths
            file_patterns = re.findall(
                r'(?:creat|modif|updat|wrote|edit|delet)\w*\s+(?:file\s+)?[`"\']?([^\s`"\']+\.\w{1,10})[`"\']?',
                content, re.IGNORECASE,
            )
            files_set.update(file_patterns)

            # Errors from tool outputs
            if msg.role == MessageRole.TOOL and any(
                kw in content.lower() for kw in ("error", "failed", "exception", "traceback")
            ):
                first_line = content.strip().split("\n")[0][:200]
                errors.append(first_line)

            # Fix #2: Decision extraction from assistant messages
            if msg.role == MessageRole.ASSISTANT:
                decisions.extend(self._extract_decisions(content))

        scope.files_changed = sorted(files_set)
        scope.errors = errors[:10]
        scope.tools_used = tools
        scope.decisions = decisions[:20]  # cap at 20

    def _extract_decisions(self, content: str) -> List[str]:
        """
        Fix #2: Extract decision-like statements from assistant messages.
        Looks for patterns like:
          - "chose X over Y"
          - "decided to ..."
          - "I'll use X because ..."
          - "going with X"
          - "decision: ..."
        """
        decisions = []
        # Pattern-based extraction (sentence-level)
        decision_patterns = [
            r'(?:chos|decid|pick|select|opt)\w+\s+.{5,80}?(?:over|instead|because|for|since)[^.!?\n]{5,120}',
            r'(?:I\'ll|we\'ll|let\'s|going to|will)\s+use\s+[^.!?\n]{5,100}',
            r'going\s+with\s+[^.!?\n]{5,80}',
            r'(?:decision|rationale|reason)\s*:\s*[^.\n]{5,150}',
        ]
        for pattern in decision_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for m in matches:
                cleaned = m.strip()[:200]
                if cleaned and cleaned not in decisions:
                    decisions.append(cleaned)
        return decisions

    # ─────────────────────────────────────────
    # Summary Generation
    # ─────────────────────────────────────────

    def _generate_summary(self, scope: ScopeRecord, messages: List[Message]) -> str:
        # Try LLM
        try:
            instructions = (
                f"Summarize this agent task execution.\n"
                f"Task: {scope.name}\n"
                f"Skill: {scope.skill_name or 'none'}\n\n"
                f"Preserve:\n"
                f"1. What was accomplished\n"
                f"2. Key decisions and rationale\n"
                f"3. Files created/modified with details\n"
                f"4. Errors and resolutions\n\n"
                f"Be concise but complete. Discard verbose tool outputs."
            )
            llm_summary = self._summarizer.summarize(
                messages,
                max_tokens=self._max_tokens,
                instructions=instructions,
            )
            if llm_summary and len(llm_summary) > 20:
                return self._format(scope, llm_summary)
        except Exception as e:
            logger.warning("LLM summary failed for '%s': %s", scope.name, e)

        return self._fallback(scope, messages)

    def _format(self, scope: ScopeRecord, llm_summary: str) -> str:
        parts = [
            f"## ✅ Scope Complete: {scope.name}",
            self._metadata_line(scope),
        ]
        if scope.files_changed:
            parts.append(f"**Files**: {', '.join(scope.files_changed[:15])}")
        if scope.tools_used:
            tool_str = ", ".join(
                f"{k}×{v}" for k, v in sorted(scope.tools_used.items(), key=lambda x: -x[1])[:8]
            )
            parts.append(f"**Tools**: {tool_str}")
        parts.append(f"\n### Summary\n{llm_summary}")
        if scope.errors:
            parts.append("### Errors\n" + "\n".join(f"- {e}" for e in scope.errors[:5]))
        return "\n".join(parts)

    def _fallback(self, scope: ScopeRecord, messages: List[Message]) -> str:
        parts = [
            f"## ✅ Scope Complete: {scope.name}",
            self._metadata_line(scope),
        ]
        if scope.tools_used:
            tool_str = ", ".join(f"{k}×{v}" for k, v in sorted(scope.tools_used.items(), key=lambda x: -x[1]))
            parts.append(f"**Tools**: {tool_str}")
        if scope.files_changed:
            parts.append("**Files**:\n" + "\n".join(f"  - {f}" for f in scope.files_changed[:20]))
        # Last assistant message as output
        assistant_msgs = [m for m in messages if m.role == MessageRole.ASSISTANT]
        if assistant_msgs:
            parts.append(f"\n### Final Output\n{assistant_msgs[-1].content[:500]}")
        if scope.errors:
            parts.append("### Errors\n" + "\n".join(f"- {e}" for e in scope.errors[:5]))
        return "\n".join(parts)

    def _metadata_line(self, scope: ScopeRecord) -> str:
        skill_tag = f" | **Skill**: {scope.skill_name}" if scope.skill_name else ""
        return (
            f"**Duration**: {scope.duration_seconds:.1f}s | "
            f"**Messages**: {scope.message_count} | "
            f"**Tools**: {sum(scope.tools_used.values())} calls"
            f"{skill_tag}"
        )
