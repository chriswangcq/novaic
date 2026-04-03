"""
Context Stack — Scope Search

Keyword-based search across scope records.
Used by both MemoryScopeStore and the memory_search tool.
"""
from __future__ import annotations

import re
from typing import List, Optional

from ..context.types import Message, MessageRole, ScopeRecord


class ScopeSearch:
    """
    Multi-field keyword search across scope records.
    
    Search targets (by level):
      L0: scope name
      L1: summary, decisions, files_changed, errors  
      L2: key assistant messages
      L3: all raw messages
    """

    def search(
        self,
        records: List[ScopeRecord],
        query: str,
        limit: int = 5,
    ) -> List[ScopeRecord]:
        """Search records by keyword, return sorted by relevance."""
        query_lower = query.lower()
        keywords = re.split(r'\s+', query_lower)

        scored: List[tuple] = []
        for record in records:
            score = self._score(record, keywords)
            if score > 0:
                scored.append((score, record.ended_at or 0, record))

        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [r for _, _, r in scored[:limit]]

    def search_within_scope(
        self,
        record: ScopeRecord,
        query: str,
    ) -> List[dict]:
        """
        Search within a single scope's content.
        Returns matching fragments with context.
        """
        query_lower = query.lower()
        results = []

        # Search in summary
        if query_lower in record.summary.lower():
            results.append({
                "source": "summary",
                "content": self._extract_context(record.summary, query_lower),
            })

        # Search in decisions
        for d in record.decisions:
            if query_lower in d.lower():
                results.append({"source": "decision", "content": d})

        # Search in files
        for f in record.files_changed:
            if query_lower in f.lower():
                results.append({"source": "file", "content": f})

        # Search in errors
        for e in record.errors:
            if query_lower in e.lower():
                results.append({"source": "error", "content": e})

        # Search in raw messages
        for msg in record.raw_messages:
            content = msg.content or ""
            if query_lower in content.lower():
                role = msg.role.value
                tool_tag = f" [{msg.tool_name}]" if msg.tool_name else ""
                results.append({
                    "source": f"message ({role}{tool_tag})",
                    "content": self._extract_context(content, query_lower, chars=300),
                })

        return results

    def _score(self, record: ScopeRecord, keywords: List[str]) -> int:
        """Score a record by keyword hits across fields."""
        score = 0

        searchable_fields = [
            (record.name, 3),           # name matches are most valuable
            (record.summary, 2),
            (" ".join(record.decisions), 2),
            (" ".join(record.files_changed), 1),
            (" ".join(record.errors), 1),
        ]

        for text, weight in searchable_fields:
            text_lower = text.lower()
            for kw in keywords:
                if kw in text_lower:
                    score += weight

        return score

    def _extract_context(
        self, text: str, query: str, chars: int = 200
    ) -> str:
        """Extract text around the query match."""
        idx = text.lower().find(query)
        if idx == -1:
            return text[:chars]
        start = max(0, idx - chars // 2)
        end = min(len(text), idx + len(query) + chars // 2)
        excerpt = text[start:end]
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(text):
            excerpt = excerpt + "..."
        return excerpt
