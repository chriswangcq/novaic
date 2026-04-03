"""
Context Stack — Recall Skill

The memory exploration skill. Injects two temporary tools into the Agent:
  - memory_expand: progressively expand scope details (L0→L1→L2→L3)
  - memory_search: keyword search across all skill results

The Agent decides how deep to explore. The engine only provides tools.

Lifecycle:
  checkpoint → inject memory tools → agent explores + works → remove tools → summarize → reload
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from ...context.types import Message, MessageRole, ScopeRecord
from ...memory.search import ScopeSearch
from ..types import Skill, SkillType

logger = logging.getLogger("context_stack.skill.recall")


class RecallSkill:
    """
    Factory + tool implementation for the Recall Skill.
    
    Creates a skill that, during pre_hooks, injects memory_expand and
    memory_search tools into the agent's toolset. During post_hooks,
    removes them.
    """

    def __init__(self, store, counter):
        """
        Args:
            store: MemoryScopeStore or MemoryBackend — where scope records live
            counter: TokenCounter — for budget awareness
        """
        self._store = store
        self._counter = counter
        self._searcher = ScopeSearch()

    def create(self, query: str = "") -> Skill:
        """Create a Recall Skill instance."""
        return Skill(
            name=f"recall:{query[:40]}" if query else "recall",
            skill_type=SkillType.RECALL,
            prompt=self._build_prompt(query),
            workflow="",
            description=f"Memory recall: {query}",
        )

    # ─────────────────────────────────────────
    # Tool Definitions (for AgentExecutor.extra_tools)
    # ─────────────────────────────────────────

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Return tool definitions to inject into the agent during recall.
        These follow the standard tool schema used by LLM APIs.
        """
        return [
            {
                "name": "memory_expand",
                "description": (
                    "Expand a past scope (task execution record) to see more details. "
                    "Use level=0 for a list of all scopes, level=1 for structured summary, "
                    "level=2 for key message fragments, level=3 for full raw messages. "
                    "Start from level 0 and drill down only as needed."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scope_id": {
                            "type": "string",
                            "description": "ID of the scope to expand. Use '' or omit for level 0 (list all scopes).",
                        },
                        "level": {
                            "type": "integer",
                            "description": "Expansion level: 0=list, 1=summary, 2=key messages, 3=full raw",
                            "default": 0,
                        },
                    },
                },
            },
            {
                "name": "memory_search",
                "description": (
                    "Search across all past scope results by keyword. "
                    "Searches in: scope names, summaries, decisions, file changes, errors, and raw messages. "
                    "Optionally limit search to a specific scope by providing scope_id."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (keywords)",
                        },
                        "scope_id": {
                            "type": "string",
                            "description": "Optional: limit search to this scope",
                        },
                    },
                    "required": ["query"],
                },
            },
        ]

    # ─────────────────────────────────────────
    # Tool Execution (called by the engine when agent invokes these tools)
    # ─────────────────────────────────────────

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Execute a recall tool call. Returns the result as string.
        
        Called by the engine's tool dispatch when agent uses 
        memory_expand or memory_search.
        """
        if tool_name == "memory_expand":
            return self._execute_expand(
                scope_id=args.get("scope_id", ""),
                level=args.get("level", 0),
            )
        elif tool_name == "memory_search":
            return self._execute_search(
                query=args.get("query", ""),
                scope_id=args.get("scope_id"),
            )
        else:
            return f"Unknown recall tool: {tool_name}"

    # ─────────────────────────────────────────
    # Tool: memory_expand
    # ─────────────────────────────────────────

    def _execute_expand(self, scope_id: str, level: int) -> str:
        """Progressive expansion of scope details."""
        
        # Level 0: List all scopes
        if not scope_id or level == 0:
            return self._expand_level_0()
        
        record = self._store.load(scope_id)
        if not record:
            return f"Scope '{scope_id}' not found."
        
        if level == 1:
            return self._expand_level_1(record)
        elif level == 2:
            return self._expand_level_2(record)
        elif level >= 3:
            return self._expand_level_3(record)
        else:
            return self._expand_level_1(record)

    def _expand_level_0(self) -> str:
        """L0: List all scopes with one-line preview."""
        records = self._store.list_all(limit=30)
        if not records:
            return "No past scopes found in memory."
        
        lines = ["## Available Scopes\n"]
        for r in records:
            summary_preview = r.summary.split("\n")[0][:80] if r.summary else "(no summary)"
            files_count = len(r.files_changed)
            tools_count = sum(r.tools_used.values())
            lines.append(
                f"- **[{r.id}]** `{r.name}` — {summary_preview}\n"
                f"  Files: {files_count} | Tools: {tools_count} | Duration: {r.duration_seconds:.0f}s"
            )
        
        lines.append(f"\n_Use memory_expand(scope_id, level=1) to see details of a specific scope._")
        return "\n".join(lines)

    def _expand_level_1(self, record: ScopeRecord) -> str:
        """L1: Structured summary (decisions, files, errors)."""
        parts = [
            f"## Scope: {record.name}",
            f"**ID**: {record.id}",
            f"**Skill**: {record.skill_name or 'meta'}",
            f"**Duration**: {record.duration_seconds:.0f}s",
            f"**Messages**: {record.message_count}",
        ]
        
        if record.files_changed:
            parts.append(f"\n### Files Changed\n" + "\n".join(f"- {f}" for f in record.files_changed))
        
        if record.tools_used:
            tool_str = ", ".join(f"{k}×{v}" for k, v in sorted(record.tools_used.items(), key=lambda x: -x[1]))
            parts.append(f"\n### Tools Used\n{tool_str}")
        
        if record.decisions:
            parts.append(f"\n### Decisions\n" + "\n".join(f"- {d}" for d in record.decisions))
        
        if record.errors:
            parts.append(f"\n### Errors\n" + "\n".join(f"- {e}" for e in record.errors))
        
        parts.append(f"\n### Summary\n{record.summary}")
        
        has_raw = bool(record.raw_messages)
        parts.append(f"\n_{'Use level=2 for key messages, level=3 for full raw.' if has_raw else 'No raw messages stored.'}_")
        
        return "\n".join(parts)

    def _expand_level_2(self, record: ScopeRecord) -> str:
        """L2: Key message fragments (assistant conclusions + important tool results)."""
        if not record.raw_messages:
            return self._expand_level_1(record) + "\n\n_(No raw messages stored for deeper expansion)_"
        
        parts = [f"## Scope: {record.name} — Key Messages\n"]
        
        for msg in record.raw_messages:
            # Include assistant messages (conclusions/decisions)
            if msg.role == MessageRole.ASSISTANT:
                content = msg.content[:500]
                parts.append(f"**[ASSISTANT]**\n{content}\n")
            
            # Include error tool results
            elif msg.role == MessageRole.TOOL and any(
                kw in (msg.content or "").lower()
                for kw in ("error", "failed", "exception")
            ):
                content = msg.content[:300]
                tool_tag = f" [{msg.tool_name}]" if msg.tool_name else ""
                parts.append(f"**[TOOL{tool_tag}]** ⚠️\n{content}\n")
            
            # Include write/create tool results (file changes)
            elif msg.role == MessageRole.TOOL and msg.tool_name and any(
                kw in msg.tool_name.lower()
                for kw in ("write", "create", "edit", "replace")
            ):
                content = msg.content[:200]
                parts.append(f"**[TOOL {msg.tool_name}]**\n{content}\n")
        
        parts.append(f"\n_Use level=3 for complete raw messages ({len(record.raw_messages)} total)._")
        return "\n".join(parts)

    def _expand_level_3(self, record: ScopeRecord) -> str:
        """L3: Full raw messages (most expensive)."""
        if not record.raw_messages:
            return self._expand_level_1(record) + "\n\n_(No raw messages stored)_"
        
        parts = [f"## Scope: {record.name} — Full Messages ({len(record.raw_messages)})\n"]
        
        for i, msg in enumerate(record.raw_messages):
            role = msg.role.value.upper()
            tool_tag = f" [{msg.tool_name}]" if msg.tool_name else ""
            # Cap individual messages at 1000 chars to prevent explosion
            content = msg.content[:1000]
            if len(msg.content) > 1000:
                content += f"\n... (truncated, was {len(msg.content)} chars)"
            parts.append(f"### [{i+1}] {role}{tool_tag}\n{content}\n")
        
        return "\n".join(parts)

    # ─────────────────────────────────────────
    # Tool: memory_search
    # ─────────────────────────────────────────

    def _execute_search(self, query: str, scope_id: Optional[str] = None) -> str:
        """Search across scope results."""
        if not query:
            return "Please provide a search query."
        
        # Search within a specific scope
        if scope_id:
            record = self._store.load(scope_id)
            if not record:
                return f"Scope '{scope_id}' not found."
            
            results = self._searcher.search_within_scope(record, query)
            if not results:
                return f"No matches for '{query}' in scope '{record.name}'."
            
            parts = [f"## Search Results for '{query}' in '{record.name}'\n"]
            for r in results[:10]:
                parts.append(f"**[{r['source']}]**\n{r['content']}\n")
            return "\n".join(parts)
        
        # Search across all scopes
        records = self._store.list_all(limit=50)
        if not records:
            return "No scopes in memory to search."
        
        matched = self._searcher.search(records, query, limit=5)
        if not matched:
            return f"No scopes matched '{query}'."
        
        parts = [f"## Search Results for '{query}'\n"]
        for record in matched:
            summary_preview = record.summary[:150] if record.summary else "(no summary)"
            parts.append(
                f"### [{record.id}] {record.name}\n"
                f"**Files**: {', '.join(record.files_changed[:5])}\n"
                f"**Preview**: {summary_preview}\n"
            )
            
            # Also show within-scope matches
            within = self._searcher.search_within_scope(record, query)
            if within:
                for w in within[:3]:
                    parts.append(f"  - [{w['source']}]: {w['content'][:100]}")
                parts.append("")
        
        parts.append(f"_Use memory_expand(scope_id, level=N) to drill into a specific scope._")
        return "\n".join(parts)

    # ─────────────────────────────────────────
    # Prompt for the Recall Skill
    # ─────────────────────────────────────────

    def _build_prompt(self, query: str) -> str:
        return (
            f"## Recall Mode\n\n"
            f"The user needs information from past work. "
            f"You have two special tools to explore memory:\n\n"
            f"1. **memory_expand(scope_id, level)** — Progressively expand past scopes:\n"
            f"   - Level 0: List all available scopes\n"
            f"   - Level 1: Structured summary of a scope\n"
            f"   - Level 2: Key messages (decisions, errors, file writes)\n"
            f"   - Level 3: Full raw messages\n\n"
            f"2. **memory_search(query, scope_id?)** — Keyword search across all past work\n\n"
            f"**Strategy**: Start with memory_search or memory_expand(level=0), "
            f"then drill down only as deep as needed. Don't expand to level 3 unless necessary.\n\n"
            f"{'**Query**: ' + query if query else ''}"
        )
