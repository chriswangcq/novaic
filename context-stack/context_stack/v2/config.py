"""
Context Stack v2 — CompactConfig

All configuration for the context engine.
New fields for v2:
  - full_prefix_validation (§4.2.3)
  - skill_end_report_validator / max_skill_end_retries (§4.6.2)
  - nested_fold_stash_threshold (§4.6.8)
  - auto_meta_when_stack_empty / auto_meta_explicit_mode (§4.6.7)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional


@dataclass
class CompactConfig:
    """Unified configuration for context engine behavior."""

    # ─── Core budget ───
    context_window: int = 200_000
    compact_threshold: float = 0.70
    emergency_threshold: float = 0.95

    # ─── Micro compaction ───
    micro_max_tool_output_chars: int = 500
    micro_preserve_recent: int = 3

    # ─── Auto compaction ───
    auto_summary_max_tokens: int = 20_000
    auto_circuit_breaker_max_fails: int = 3

    # ─── Scope storage ───
    scope_store_raw: bool = True
    raw_max_chars_per_scope: int = 50_000

    # ─── Prefix validation (§4.2.3) ───
    full_prefix_validation: bool = False  # True = O(n) deep compare; False = hash fast path

    # ─── Skill stack (§4.6.7) ───
    auto_meta_when_stack_empty: bool = True
    auto_meta_explicit_mode: Literal["stack_under", "replace_when_only_auto"] = "stack_under"
    max_skill_depth: int = 4

    # ─── Skill End Report (§4.6.2) ───
    # Validator is set programmatically, not via config value
    max_skill_end_retries: int = 1
    skill_end_empty_fallback: Literal["stub", "engine_summarize"] = "stub"

    # ─── Nested fold (§4.6.8) ───
    nested_skill_fold: bool = False
    nested_fold_summarizer: Literal["stub", "llm"] = "stub"
    nested_fold_max_chars: int = 500
    nested_fold_stash_threshold: int = 30_000  # chars; above this → external storage
    nested_fold_instructions: str = ""

    # ─── Gem Fusion (宝石合成 / 消消乐) ───
    gem_fusion_enabled: bool = False           # Enable N-ary scope fusion
    gem_fusion_merge_factor: int = 5           # N scopes → 1 next-level (base of carry)
    gem_fusion_max_level: int = 10             # Safety cap on fusion depth
