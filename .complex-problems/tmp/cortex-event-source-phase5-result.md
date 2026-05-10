# Phase 5 result: legacy cleanup, reset behavior, and full verification

## Summary

Phase 5 completed the final full-cut cleanup around Cortex LLM context assembly. The active read path is event-projected, legacy DFS fallback behavior now fails with explicit reset-required semantics, source-of-truth language was cleaned up, and a strict final review forced physical deletion of the old DFS renderer and direct tests.

## Done

- Completed legacy DFS deletion inventory.
- Added no-compat reset behavior tests for legacy-only roots.
- Cleaned source-of-truth language so active LLM context assembly is described as event-projected.
- Verified active `prepare_for_llm` and usage/status read paths use `ContextEventReadModel`.
- Physically deleted:
  - `novaic_cortex/context_stack/engine.py`
  - `novaic_cortex/context_stack/step_tree.py`
  - direct legacy DFS renderer tests.
- Removed `ContextEngine`, `StepTree`, `StepNode`, and `StepTreeBuilder` active exports.
- Migrated remaining invariant coverage to event-written API context plus `context_prepare_for_llm`.
- Added projection behavior for active wake close summary folding and system prompt ordering.

## Evidence

Final production old-symbol scan:

```bash
rg -n "ContextEngine|StepTree|prepare_messages_for_llm|context_stack\\.engine|context_stack\\.step_tree" novaic-cortex/novaic_cortex
```

Result: no matches.

Final focused tests: `41 passed`.

Final full Cortex tests:

```text
430 passed
```

## Child Results

- P058: Legacy DFS deletion inventory succeeded.
- P059: Old data reset/no-compat behavior succeeded.
- P060: Source-of-truth language/artifact cleanup succeeded.
- P061: Final verification initially found physical residue, then succeeded after P062 follow-up.
- P062: Physically deleted legacy DFS renderer and direct tests.

## Residual Risk

Only source-guard test strings mention the old renderer symbols. They are intentional guardrails, not compatibility code.
