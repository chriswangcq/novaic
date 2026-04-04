"""
Context Stack v2 — Recall Skill (Tree-based ID Navigation)

Memory exploration via a single tool:
  - memory_expand(id): expand one level deeper, revealing child IDs

Design principles:
  1. Every expandable node has a hierarchical ID embedded in the context
  2. memory_expand(id) always expands exactly ONE level
  3. The returned content contains the next-level child IDs for further drilling
  4. Completely stateless — the ID encodes the full path, no hidden state tracking

ID scheme:
  - ""               → list all root scopes  (each has id like "abc123")
  - "abc123"         → scope overview: summary + child node IDs
  - "abc123.meta"    → structured metadata (decisions, tools, errors)
  - "abc123.files"   → file change list
  - "abc123.messages" → key messages with individual message IDs
  - "abc123.msg.3"   → full content of message #3

This is fundamentally a virtual filesystem / tree browser.
The LLM navigates by calling expand(child_id) on IDs it sees in context.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from .types import Message, MessageRole, ScopeRecord

logger = logging.getLogger("context_stack.v2.recall")


# ─────────────────────────────────────────────
# ID path parsing
# ─────────────────────────────────────────────

def _parse_expand_id(expand_id: str) -> dict:
    """
    Parse a hierarchical expand ID into components.

    Returns dict with:
      - scope_id: str or "" (root listing)
      - segment: str — "root" | "overview" | "meta" | "files" | "messages" | "msg"
      - msg_index: int or None — for "msg" segment
    """
    expand_id = expand_id.strip()
    if not expand_id:
        return {"scope_id": "", "segment": "root", "msg_index": None}

    parts = expand_id.split(".")

    if len(parts) == 1:
        # "abc123" → scope overview
        return {"scope_id": parts[0], "segment": "overview", "msg_index": None}
    elif len(parts) == 2:
        scope_id, segment = parts
        if segment in ("meta", "files", "messages"):
            return {"scope_id": scope_id, "segment": segment, "msg_index": None}
        else:
            return {"scope_id": scope_id, "segment": segment, "msg_index": None}
    elif len(parts) == 3 and parts[1] == "msg":
        # "abc123.msg.3"
        try:
            idx = int(parts[2])
        except ValueError:
            idx = None
        return {"scope_id": parts[0], "segment": "msg", "msg_index": idx}
    else:
        # Unknown structure — treat as scope_id
        return {"scope_id": expand_id, "segment": "overview", "msg_index": None}


class RecallSkill:
    """
    Stateless tree-based memory navigation.

    Key design:
      - expand(id) takes a SINGLE ID parameter
      - Each expansion returns content with embedded child IDs
      - No internal expansion state — the ID IS the state
      - The LLM picks which child ID to expand next based on context

    Usage in ToolRouter:
        result = recall.execute_tool("memory_expand", {"id": "abc123.files"})
        # result is a string to inject as SYSTEM context message
    """

    def __init__(self, store, counter=None):
        """
        Args:
            store: MemoryBackend / InMemoryScopeStore — where scope records live
            counter: optional TokenCounter for budget awareness
        """
        self._store = store
        self._counter = counter

    # ─────────────────────────────────────────
    # Tool Definitions
    # ─────────────────────────────────────────

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return tool definitions for injection into LLM extra_tools."""
        return [
            {
                "name": "memory_expand",
                "description": (
                    "Expand a node from memory to see more details. "
                    "Pass the ID that appears in the current context "
                    "(e.g., [abc123], [abc123.files], [abc123.msg.3]).\n"
                    "Each call expands exactly one level and reveals "
                    "child IDs for further drilling.\n"
                    "Omit the id to list all available scopes."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": (
                                "Hierarchical node ID from the context. "
                                "Examples: 'abc123', 'abc123.meta', "
                                "'abc123.files', 'abc123.messages', "
                                "'abc123.msg.3'. Omit to list root scopes."
                            ),
                        },
                    },
                },
            },
            {
                "name": "memory_search",
                "description": (
                    "Search across all past scope results by keyword. "
                    "Searches scope names, summaries, decisions, file changes, "
                    "and raw messages. Results are injected into context."
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
    # Tool Execution
    # ─────────────────────────────────────────

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Execute a recall tool call. Returns result as string."""
        if tool_name == "memory_expand":
            return self._execute_expand(
                expand_id=args.get("id", ""),
            )
        elif tool_name == "memory_search":
            return self._execute_search(
                query=args.get("query", ""),
                scope_id=args.get("scope_id"),
            )
        else:
            return f"Unknown recall tool: {tool_name}"

    # ─────────────────────────────────────────
    # memory_expand (tree navigation)
    # ─────────────────────────────────────────

    def _execute_expand(self, expand_id: str) -> str:
        """
        Stateless tree expansion: parse the ID, fetch the right slice.

        ID routing:
          ""               → _expand_root()       — list all scopes
          "abc123"         → _expand_overview()    — scope summary + child IDs
          "abc123.meta"    → _expand_meta()        — decisions, tools, errors
          "abc123.files"   → _expand_files()       — file change list
          "abc123.messages"→ _expand_messages()    — key message list + msg IDs
          "abc123.msg.N"   → _expand_single_msg()  — full content of message N
        """
        parsed = _parse_expand_id(expand_id)
        segment = parsed["segment"]
        scope_id = parsed["scope_id"]

        logger.info(
            "memory_expand: id=%r → scope=%s segment=%s",
            expand_id, scope_id, segment,
        )

        if segment == "root":
            return self._expand_root()

        # Load the scope record
        record = self._store.load(scope_id)
        if not record:
            return f"Node '{expand_id}' not found. Scope '{scope_id}' does not exist in memory."

        if segment == "overview":
            return self._expand_overview(record)
        elif segment == "meta":
            return self._expand_meta(record)
        elif segment == "files":
            return self._expand_files(record)
        elif segment == "messages":
            return self._expand_messages(record)
        elif segment == "msg":
            return self._expand_single_msg(record, parsed["msg_index"])
        else:
            return f"Unknown segment '{segment}' in ID '{expand_id}'."

    # ─────────────────────────────────────────
    # Tree node renderers
    # ─────────────────────────────────────────

    def _expand_root(self) -> str:
        """List all available scopes with one-line preview."""
        records = self._store.list_all(limit=30)
        if not records:
            return "No past scopes found in memory."

        lines = ["## 📂 Available Scopes\n"]
        for r in records:
            summary_preview = (
                r.summary.split("\n")[0][:80] if r.summary else "(no summary)"
            )
            files_count = len(r.files_changed)
            lines.append(
                f"- **[{r.id}]** `{r.name}` — {summary_preview}\n"
                f"  Files: {files_count} | "
                f"Duration: {r.duration_seconds:.0f}s"
            )

        lines.append(
            "\n_Call `memory_expand(id)` with any scope ID above to drill in._"
        )
        return "\n".join(lines)

    def _expand_overview(self, record: ScopeRecord) -> str:
        """
        Scope overview: summary + list of expandable child nodes.
        This is the first drill-in from root.
        """
        sid = record.id
        parts = [
            f"## 📋 Scope: {record.name}",
            f"**ID**: `{sid}`",
            f"**Skill**: {record.skill_name or 'meta'}",
            f"**Duration**: {record.duration_seconds:.0f}s",
            f"**Messages**: {record.message_count}",
        ]

        if record.summary:
            # Show the summary inline (it's compact enough)
            parts.append(f"\n### Summary\n{record.summary}")

        # List expandable child nodes with their IDs
        parts.append("\n### Expandable Sections")

        children = []
        if record.decisions or record.tools_used or record.errors:
            meta_items = []
            if record.decisions:
                meta_items.append(f"{len(record.decisions)} decisions")
            if record.tools_used:
                meta_items.append(f"{len(record.tools_used)} tool types")
            if record.errors:
                meta_items.append(f"{len(record.errors)} errors")
            children.append(
                f"- **[{sid}.meta]** Metadata — {', '.join(meta_items)}"
            )

        if record.files_changed:
            children.append(
                f"- **[{sid}.files]** Files Changed — {len(record.files_changed)} files"
            )

        if record.raw_messages:
            children.append(
                f"- **[{sid}.messages]** Messages — {len(record.raw_messages)} messages"
            )

        if children:
            parts.extend(children)
        else:
            parts.append("_(No further detail available for this scope.)_")

        parts.append(
            "\n_Call `memory_expand(child_id)` to drill into any section above._"
        )
        return "\n".join(parts)

    def _expand_meta(self, record: ScopeRecord) -> str:
        """Metadata detail: decisions, tools used, errors."""
        sid = record.id
        parts = [f"## 🔧 Metadata: {record.name} [{sid}.meta]"]

        if record.decisions:
            parts.append(
                "\n### Decisions\n" +
                "\n".join(f"- {d}" for d in record.decisions)
            )

        if record.tools_used:
            tool_str = ", ".join(
                f"{k}×{v}" for k, v in
                sorted(record.tools_used.items(), key=lambda x: -x[1])
            )
            parts.append(f"\n### Tools Used\n{tool_str}")

        if record.errors:
            parts.append(
                "\n### Errors\n" +
                "\n".join(f"- ⚠️ {e}" for e in record.errors)
            )

        if not (record.decisions or record.tools_used or record.errors):
            parts.append("_(No metadata recorded for this scope.)_")

        # Sibling navigation hints
        siblings = []
        if record.files_changed:
            siblings.append(f"[{sid}.files]")
        if record.raw_messages:
            siblings.append(f"[{sid}.messages]")
        if siblings:
            parts.append(f"\n_Siblings: {', '.join(siblings)}_")

        return "\n".join(parts)

    def _expand_files(self, record: ScopeRecord) -> str:
        """File change list for this scope."""
        sid = record.id
        parts = [f"## 📁 Files Changed: {record.name} [{sid}.files]"]

        if record.files_changed:
            parts.append("")
            for f in record.files_changed:
                parts.append(f"- `{f}`")
        else:
            parts.append("_(No file changes recorded.)_")

        # Sibling navigation hints
        siblings = []
        if record.decisions or record.tools_used or record.errors:
            siblings.append(f"[{sid}.meta]")
        if record.raw_messages:
            siblings.append(f"[{sid}.messages]")
        if siblings:
            parts.append(f"\n_Siblings: {', '.join(siblings)}_")

        return "\n".join(parts)

    def _expand_messages(self, record: ScopeRecord) -> str:
        """
        Message listing: show role + preview for each message,
        with per-message IDs for further expansion.
        """
        sid = record.id
        parts = [
            f"## 💬 Messages: {record.name} [{sid}.messages]",
            f"_({len(record.raw_messages)} messages total)_\n",
        ]

        if not record.raw_messages:
            parts.append("_(No raw messages stored.)_")
            return "\n".join(parts)

        for i, msg in enumerate(record.raw_messages):
            role = msg.role.value.upper()
            tool_tag = f" [{msg.tool_name}]" if msg.tool_name else ""

            # Short preview (first 120 chars)
            preview = (msg.content or "")[:120].replace("\n", " ")
            if len(msg.content or "") > 120:
                preview += "..."

            parts.append(
                f"- **[{sid}.msg.{i}]** `{role}{tool_tag}` — {preview}"
            )

        parts.append(
            f"\n_Call `memory_expand(\"{sid}.msg.N\")` to see full message content._"
        )
        return "\n".join(parts)

    def _expand_single_msg(self, record: ScopeRecord, msg_index: Optional[int]) -> str:
        """Full content of a single message by index."""
        sid = record.id

        if msg_index is None:
            return f"Invalid message index in ID. Use format: {sid}.msg.0, {sid}.msg.1, etc."

        if not record.raw_messages:
            return f"Scope '{record.name}' [{sid}]: no raw messages stored."

        if msg_index < 0 or msg_index >= len(record.raw_messages):
            return (
                f"Message index {msg_index} out of range. "
                f"Valid range: 0–{len(record.raw_messages) - 1}."
            )

        msg = record.raw_messages[msg_index]
        role = msg.role.value.upper()
        tool_tag = f" [{msg.tool_name}]" if msg.tool_name else ""

        content = msg.content or "(empty)"
        # Cap at 2000 chars for safety
        if len(content) > 2000:
            content = content[:2000] + f"\n... (truncated, was {len(content)} chars)"

        parts = [
            f"## 📝 Message #{msg_index}: {role}{tool_tag}",
            f"**Scope**: {record.name} [{sid}]",
            f"",
            content,
        ]

        # Navigation: prev/next message hints
        nav = []
        if msg_index > 0:
            nav.append(f"[{sid}.msg.{msg_index - 1}] (prev)")
        if msg_index < len(record.raw_messages) - 1:
            nav.append(f"[{sid}.msg.{msg_index + 1}] (next)")
        if nav:
            parts.append(f"\n_Navigate: {', '.join(nav)}_")

        return "\n".join(parts)

    # ─────────────────────────────────────────
    # memory_search
    # ─────────────────────────────────────────

    def _execute_search(
        self,
        query: str,
        scope_id: Optional[str] = None,
    ) -> str:
        """Search across scope results."""
        if not query:
            return "Please provide a search query."

        if scope_id:
            record = self._store.load(scope_id)
            if not record:
                return f"Scope '{scope_id}' not found."

            results = self._search_within_scope(record, query)
            if not results:
                return f"No matches for '{query}' in scope '{record.name}'."

            parts = [f"## Search Results for '{query}' in '{record.name}'\n"]
            for r in results[:10]:
                parts.append(f"**[{r['source']}]**\n{r['content']}\n")

            # Suggest expansion
            parts.append(
                f"\n_Use `memory_expand(\"{scope_id}\")` to drill into this scope._"
            )
            return "\n".join(parts)

        # Search across all scopes
        records = self._store.list_all(limit=50)
        if not records:
            return "No scopes in memory to search."

        matched = self._keyword_search(records, query, limit=5)
        if not matched:
            return f"No scopes matched '{query}'."

        parts = [f"## Search Results for '{query}'\n"]
        for record in matched:
            summary_preview = (
                record.summary[:150] if record.summary else "(no summary)"
            )
            parts.append(
                f"### [{record.id}] {record.name}\n"
                f"**Files**: {', '.join(record.files_changed[:5])}\n"
                f"**Preview**: {summary_preview}\n"
            )

            within = self._search_within_scope(record, query)
            if within:
                for w in within[:3]:
                    parts.append(
                        f"  - [{w['source']}]: {w['content'][:100]}"
                    )
                parts.append("")

        parts.append(
            "_Use `memory_expand(scope_id)` to drill into any matched scope._"
        )
        return "\n".join(parts)

    # ─────────────────────────────────────────
    # Search helpers
    # ─────────────────────────────────────────

    def _keyword_search(
        self,
        records: List[ScopeRecord],
        query: str,
        limit: int = 5,
    ) -> List[ScopeRecord]:
        """Multi-field keyword search across scope records."""
        query_lower = query.lower()
        keywords = re.split(r'\s+', query_lower)

        scored = []
        for record in records:
            score = self._score(record, keywords)
            if score > 0:
                scored.append((score, record.ended_at or 0, record))

        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [r for _, _, r in scored[:limit]]

    def _score(self, record: ScopeRecord, keywords: List[str]) -> int:
        """Score a record by keyword hits."""
        score = 0
        fields = [
            (record.name, 3),
            (record.summary, 2),
            (" ".join(record.decisions), 2),
            (" ".join(record.files_changed), 1),
            (" ".join(record.errors), 1),
        ]
        for text, weight in fields:
            text_lower = text.lower()
            for kw in keywords:
                if kw in text_lower:
                    score += weight
        return score

    def _search_within_scope(
        self,
        record: ScopeRecord,
        query: str,
    ) -> List[Dict[str, str]]:
        """Search within a single scope's content."""
        query_lower = query.lower()
        results = []

        if query_lower in record.summary.lower():
            results.append({
                "source": "summary",
                "content": self._extract_context(record.summary, query_lower),
            })

        for d in record.decisions:
            if query_lower in d.lower():
                results.append({"source": "decision", "content": d})

        for f in record.files_changed:
            if query_lower in f.lower():
                results.append({"source": "file", "content": f})

        for e in record.errors:
            if query_lower in e.lower():
                results.append({"source": "error", "content": e})

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

    def _extract_context(
        self,
        text: str,
        query: str,
        chars: int = 200,
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

    # ─────────────────────────────────────────
    # Prompt
    # ─────────────────────────────────────────

    def build_prompt(self, query: str = "") -> str:
        """Build the recall system prompt."""
        return (
            "## Recall Mode\n\n"
            "You have two special tools to explore memory:\n\n"
            "1. **memory_expand(id)** — Expand a node by its ID:\n"
            "   - Omit id: list all available past scopes\n"
            "   - Scope ID (e.g. `abc123`): show overview + child node IDs\n"
            "   - Child ID (e.g. `abc123.meta`, `abc123.files`, `abc123.messages`): "
            "drill into that section\n"
            "   - Message ID (e.g. `abc123.msg.3`): show full message content\n"
            "   - Each call expands exactly one level and reveals next-level IDs\n\n"
            "2. **memory_search(query, scope_id?)** — Keyword search across all past work\n\n"
            "**Strategy**: Start with `memory_expand()` to list scopes, "
            "then drill into specific nodes by their IDs.\n\n"
            f"{'**Query**: ' + query if query else ''}"
        )
