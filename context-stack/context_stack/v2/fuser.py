"""
Context Stack v2 — Scope Fuser (宝石合成 / 消消乐)

Progressive summarization via N-ary carry (default: 5-ary).

Metaphor:
  - Level 0: Raw skill scopes (individual gems)
  - Level 1: 5 × L0 scopes fused into 1 mega-summary  (★)
  - Level 2: 5 × L1 scopes fused into 1 ultra-summary (★★)
  - Level 3: 5 × L2 scopes fused into 1 giga-summary  (★★★)
  - ...

Like 消消乐 (match-and-merge) or base-5 carry:
  When N scopes exist at the same level → fuse → emit 1 next-level scope.
  This cascades: if fusing L0→L1 fills the L1 bucket, auto-fuse L1→L2.

Benefits:
  - O(log_N(total_scopes)) active summaries instead of O(total_scopes)
  - Each level is a denser, more abstracted view of history
  - Children are preserved for drill-down (progressive disclosure)

Design decisions:
  - Fused scope keeps children_ids for traceability
  - Children are marked state=FUSED (archived), not deleted
  - Fused scope summary = synthesis of children summaries
  - No LLM call by default (concatenation + metadata); pluggable Summarizer
  - Cascade is automatic and depth-unlimited
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Callable, Dict, List, Optional, Tuple

from .types import ScopeRecord, ScopeState

logger = logging.getLogger("context_stack.v2.fuser")


def _default_fuse_fn(children: List[ScopeRecord], level: int) -> str:
    """
    Default fusion function: structured extraction (no LLM).

    Produces a markdown summary that synthesizes key information:
      1. Timeline overview
      2. Key decisions & outcomes
      3. Files and tools usage
      4. Error patterns
      5. Synthesis conclusion

    This is designed to be useful standalone but also easy to replace
    with an LLM-based fuser for higher quality output.
    """
    stars = "★" * level
    header = f"## {stars} Level {level} Fusion ({len(children)} scopes merged)"

    parts = [header, ""]

    # ── 1. Aggregate metadata ──
    all_files: set = set()
    all_tools: Dict[str, int] = {}
    all_decisions: list = []
    all_errors: list = []
    total_tokens_saved = 0
    total_message_count = 0
    child_names = []

    for child in children:
        child_names.append(child.name or child.skill_name or child.id)
        all_files.update(child.files_changed)
        for tool, count in child.tools_used.items():
            all_tools[tool] = all_tools.get(tool, 0) + count
        all_decisions.extend(child.decisions)
        all_errors.extend(child.errors)
        total_tokens_saved += child.tokens_saved
        total_message_count += child.message_count

    # ── 2. Timeline overview ──
    duration = (children[-1].ended_at or time.time()) - children[0].started_at
    parts.append(
        f"**Scopes merged**: {len(children)} | "
        f"**Total duration**: {duration:.0f}s | "
        f"**Messages processed**: {total_message_count} | "
        f"**Tokens saved**: {total_tokens_saved:,}"
    )
    parts.append(f"**Timeline**: {' → '.join(child_names)}")
    parts.append("")

    # ── 3. Synthesized accomplishments ──
    parts.append("### Accomplishments")
    for i, child in enumerate(children, 1):
        name = child.name or child.id
        # Extract first meaningful sentence from summary
        first_line = ""
        if child.summary:
            for line in child.summary.split("\n"):
                line = line.strip().lstrip("#").lstrip("*").strip()
                if line and len(line) > 10 and not line.startswith("["):
                    first_line = line[:200]
                    break
        if not first_line:
            first_line = f"Completed {child.skill_name or 'task'}"
        parts.append(f"{i}. **{name}**: {first_line}")
    parts.append("")

    # ── 4. Key decisions (deduplicated) ──
    if all_decisions:
        seen = set()
        unique_decisions = []
        for d in all_decisions:
            d_lower = d.lower().strip()
            if d_lower not in seen:
                seen.add(d_lower)
                unique_decisions.append(d)
        parts.append("### Key Decisions")
        for d in unique_decisions[:10]:
            parts.append(f"- {d}")
        parts.append("")

    # ── 5. Files changed (grouped by directory) ──
    if all_files:
        parts.append(f"### Files Changed ({len(all_files)} files)")
        # Group by top-level directory
        dir_groups: Dict[str, list] = {}
        for f in sorted(all_files):
            dirname = f.split("/")[0] if "/" in f else "."
            dir_groups.setdefault(dirname, []).append(f)
        for dirname, files in sorted(dir_groups.items()):
            if len(files) <= 3:
                parts.append(f"- `{dirname}/`: {', '.join(f.split('/')[-1] for f in files)}")
            else:
                parts.append(f"- `{dirname}/`: {len(files)} files")
        parts.append("")

    # ── 6. Tool usage (top N) ──
    if all_tools:
        sorted_tools = sorted(all_tools.items(), key=lambda x: -x[1])[:8]
        tool_str = ", ".join(f"{k}×{v}" for k, v in sorted_tools)
        parts.append(f"### Tools: {tool_str}")
        parts.append("")

    # ── 7. Errors & issues ──
    if all_errors:
        seen_errors = set()
        unique_errors = []
        for e in all_errors:
            e_key = e.lower()[:50]
            if e_key not in seen_errors:
                seen_errors.add(e_key)
                unique_errors.append(e)
        parts.append(f"### Issues Encountered ({len(unique_errors)})")
        for e in unique_errors[:5]:
            parts.append(f"- ⚠️ {e[:200]}")
        parts.append("")

    # ── 8. Synthesis conclusion ──
    parts.append("### Synthesis")
    if all_errors:
        parts.append(
            f"Across {len(children)} scopes, {len(all_files)} files were modified "
            f"with {len(set(all_errors))} issue(s) encountered and resolved. "
            f"Primary tools: {', '.join(k for k, _ in sorted_tools[:3]) if all_tools else 'none'}."
        )
    else:
        parts.append(
            f"Across {len(children)} scopes, {len(all_files)} files were modified successfully. "
            f"No errors encountered. "
            f"Primary tools: {', '.join(k for k, _ in sorted_tools[:3]) if all_tools else 'none'}."
        )

    return "\n".join(parts)


class ScopeFuser:
    """
    Gem Fusion Engine (宝石合成器).

    Watches for N same-level scopes and fuses them into 1 next-level scope.
    Cascades automatically: if fusing L0→L1 completes a L1 bucket, fuses L1→L2.

    Usage:
        fuser = ScopeFuser(store=my_store, merge_factor=5)
        engine.hooks.register("post_finalize", lambda scope: fuser.maybe_fuse(scope))

        # Or call manually after scope completion:
        fused = fuser.maybe_fuse(completed_scope)

        # Inspect fusion tree:
        tree = fuser.get_fusion_tree(scope_id)
    """

    def __init__(
        self,
        store,
        merge_factor: int = 5,
        fuse_fn: Optional[Callable[[List[ScopeRecord], int], str]] = None,
        max_level: int = 10,
    ):
        """
        Args:
            store: MemoryBackend that stores ScopeRecords
            merge_factor: N scopes at same level → 1 next-level scope (default: 5)
            fuse_fn: custom function to generate fused summary
                     signature: (children, target_level) → str
            max_level: cap on fusion depth (safety valve)
        """
        if merge_factor < 2:
            raise ValueError("merge_factor must be ≥ 2")

        self._store = store
        self._merge_factor = merge_factor
        self._fuse_fn = fuse_fn or _default_fuse_fn
        self._max_level = max_level

        # Stats
        self.total_fusions = 0
        self.max_level_reached = 0

    def maybe_fuse(self, trigger_scope: ScopeRecord) -> List[ScopeRecord]:
        """
        Check if fusion should occur after a scope completes.

        Called after each scope finalization. Cascades automatically.

        Args:
            trigger_scope: the just-completed scope

        Returns:
            list of newly created fused scopes (empty if no fusion occurred)
        """
        level = trigger_scope.level
        all_fused = []

        while level < self._max_level:
            # Count unfused scopes at this level
            candidates = self._get_unfused_at_level(level)
            if len(candidates) < self._merge_factor:
                break

            # Take the oldest N scopes for fusion
            to_fuse = candidates[:self._merge_factor]
            fused = self._fuse(to_fuse, level + 1)
            all_fused.append(fused)

            logger.info(
                "🔮 Gem Fusion: %d × L%d → L%d (id=%s, '%s')",
                len(to_fuse), level, level + 1, fused.id, fused.name,
            )

            level += 1  # Check if this new level also needs fusion

        return all_fused

    def force_fuse_level(self, level: int) -> Optional[ScopeRecord]:
        """
        Force fusion of all unfused scopes at a given level,
        even if fewer than merge_factor are available.

        Useful for session-end cleanup.

        Returns:
            fused scope, or None if nothing to fuse
        """
        candidates = self._get_unfused_at_level(level)
        if len(candidates) < 2:
            return None  # Need at least 2 to fuse

        fused = self._fuse(candidates, level + 1)
        logger.info(
            "🔮 Forced fusion: %d × L%d → L%d (id=%s, '%s')",
            len(candidates), level, level + 1, fused.id, fused.name,
        )
        return fused

    def fuse_all_remaining(self) -> List[ScopeRecord]:
        """
        Force-fuse all remaining unfused scopes at every level.
        Called at session end to produce a minimal set of top-level summaries.

        Returns:
            list of all newly fused scopes
        """
        all_fused = []
        for level in range(self._max_level):
            result = self.force_fuse_level(level)
            if result:
                all_fused.append(result)
            elif not self._get_unfused_at_level(level):
                # No scopes at this level or above → done
                if not any(
                    self._get_unfused_at_level(l)
                    for l in range(level + 1, min(level + 3, self._max_level))
                ):
                    break
        return all_fused

    def _get_unfused_at_level(self, level: int) -> List[ScopeRecord]:
        """
        Get all unfused (state=COMPACTED) scopes at a specific level.
        Ordered by ended_at ascending (oldest first → FIFO fusion).
        """
        all_compacted = self._store.list_all(limit=500)
        at_level = [
            r for r in all_compacted
            if r.level == level and r.state == ScopeState.COMPACTED
        ]
        # Sort by ended_at ascending (oldest first)
        at_level.sort(key=lambda r: r.ended_at or 0)
        return at_level

    def _fuse(self, children: List[ScopeRecord], target_level: int) -> ScopeRecord:
        """
        Fuse N children into a single parent scope at target_level.
        """
        # Generate fused summary
        summary = self._fuse_fn(children, target_level)

        # Aggregate metadata
        all_files = set()
        all_tools: Dict[str, int] = {}
        all_decisions = []
        all_errors = []
        total_tokens_saved = 0
        total_messages = 0

        for child in children:
            all_files.update(child.files_changed)
            for tool, count in child.tools_used.items():
                all_tools[tool] = all_tools.get(tool, 0) + count
            all_decisions.extend(child.decisions[:3])  # Keep top 3 per child
            all_errors.extend(child.errors[:2])
            total_tokens_saved += child.tokens_saved
            total_messages += child.message_count

        # Build fused scope name
        child_names = [c.name or c.id for c in children]
        if len(child_names) <= 3:
            fused_name = " + ".join(child_names)
        else:
            fused_name = f"{child_names[0]} + ... + {child_names[-1]} ({len(children)} scopes)"

        fused = ScopeRecord(
            name=fused_name,
            skill_name="__fusion__",
            state=ScopeState.COMPACTED,
            started_at=children[0].started_at,
            ended_at=children[-1].ended_at,
            summary=summary,
            decisions=all_decisions[:15],
            files_changed=sorted(all_files)[:30],
            errors=all_errors[:10],
            tools_used=all_tools,
            message_count=total_messages,
            tokens_saved=total_tokens_saved,
            level=target_level,
            children_ids=[c.id for c in children],
        )

        # Mark children as FUSED + set parent_id
        for child in children:
            child.state = ScopeState.FUSED
            child.parent_id = fused.id
            self._store.save(child)

        # Save fused scope
        self._store.save(fused)

        # Stats
        self.total_fusions += 1
        self.max_level_reached = max(self.max_level_reached, target_level)

        return fused

    # ─────────────────────────────────────────
    # Query helpers
    # ─────────────────────────────────────────

    def get_level_counts(self) -> Dict[int, int]:
        """
        Get count of unfused (COMPACTED) scopes at each level.

        Returns:
            {level: count} — only levels with >0 scopes
        """
        all_compacted = self._store.list_all(limit=500)
        counts: Dict[int, int] = {}
        for r in all_compacted:
            if r.state == ScopeState.COMPACTED:
                counts[r.level] = counts.get(r.level, 0) + 1
        return counts

    def get_top_summaries(self) -> List[ScopeRecord]:
        """
        Get only the top-level (unfused) summaries.
        These are the "active gems" the user/system should see.
        """
        all_compacted = self._store.list_all(limit=500)
        return [
            r for r in all_compacted
            if r.state == ScopeState.COMPACTED
        ]

    def get_fusion_tree(self, scope_id: str) -> Dict:
        """
        Build the fusion tree for a scope (drill-down).

        Returns a nested dict:
          {
            "scope": {...},
            "children": [
              {"scope": {...}, "children": [...]},
              ...
            ]
          }
        """
        scope = self._store.load(scope_id)
        if not scope:
            return {"scope": None, "children": []}

        tree = {
            "scope": {
                "id": scope.id,
                "name": scope.name,
                "level": scope.level,
                "state": scope.state.value,
                "summary": scope.summary[:200],
            },
            "children": [],
        }

        for child_id in scope.children_ids:
            tree["children"].append(self.get_fusion_tree(child_id))

        return tree

    def get_stats(self) -> Dict:
        """Fusion engine statistics."""
        level_counts = self.get_level_counts()
        return {
            "merge_factor": self._merge_factor,
            "total_fusions": self.total_fusions,
            "max_level_reached": self.max_level_reached,
            "level_counts": level_counts,
            "active_gems": sum(level_counts.values()),
        }
