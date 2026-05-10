# Source-of-truth language cleanup completed

## Summary

Cleaned misleading source-of-truth wording around materialized context artifacts. Remaining `context.jsonl`, `steps`, and `summary.md` references are framed as projection/debug/inspection/operational artifacts or explicit legacy DFS tests, not active LLM source semantics.

## Done

- Rewrote workspace context helper docstrings to say materialized context projection.
- Rewrote API comments for context append and archived scope labels to say projection/archive label source.
- Rewrote status docstring to describe `_collect_active_stack` as operational control-plane stack, not authoritative LLM source.
- Reworded PR-234 test docstring to event-projected control stack.

## Verification

- Static scans reviewed remaining `source-of-truth`, `authoritative`, `context.jsonl`, `steps`, and `summary.md` references.
- Guard tests: `2 passed`.
- Full Cortex suite: `455 passed`.

## Residual Risk

- Legacy DFS module comments still describe DFS internals because those modules physically remain. They are labeled legacy/debug and will be addressed by deletion/migration work.
