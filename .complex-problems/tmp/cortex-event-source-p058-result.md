# Legacy DFS deletion inventory completed

## Summary

Completed the DFS deletion inventory. No active API/runtime LLM read dependency on DFS remains. The remaining DFS surface is physically concentrated and can be deleted after migrating/removing its legacy tests.

## Static Scan Evidence

- `rg -l "ContextEngine|StepTree|prepare_messages_for_llm" novaic-cortex/novaic_cortex novaic-cortex/tests`
  - `novaic_cortex/context_stack/engine.py`
  - `novaic_cortex/context_stack/step_tree.py`
  - `novaic_cortex/context_stack/__init__.py`
  - `tests/test_context_engine_dfs.py`
  - `tests/test_pr66_system_scope_rendering.py`
  - `tests/test_pr73_folded_scope_rendering.py`
  - `tests/test_pr84_minimal_structure_invariants.py`
  - guard/default-status tests that assert DFS is absent or not used on default status.

## Classification

- Active API read source: no DFS usage found. Guard tests cover prepare/status sections.
- Runtime prepare flow: no direct DFS usage found; Runtime depends on Cortex prepare endpoint, now event-backed.
- Legacy/debug renderer:
  - `novaic_cortex/context_stack/engine.py`
  - `novaic_cortex/context_stack/step_tree.py`
  - `novaic_cortex/context_stack/__init__.py` engine/tree exports
- Legacy/debug tests to migrate or delete before physical DFS removal:
  - `tests/test_context_engine_dfs.py`
  - `tests/test_pr66_system_scope_rendering.py`
  - `tests/test_pr73_folded_scope_rendering.py`
  - the direct `ContextEngine` test block in `tests/test_pr84_minimal_structure_invariants.py`
- Shared code that must remain or be moved before deleting the package:
  - `context_stack/types.py`
  - `context_stack/budget.py`
  These are used by the event read model for budget/status.
- Materialized projection/inspection artifacts, not DFS source-of-truth:
  - `Workspace.read_context`, `context_read`, `context_append_projection`, `summary.md` assertions, archive/list tests.

## Deletion Plan

1. Migrate or delete legacy DFS tests listed above.
2. Move or keep `types.py` and `budget.py` as active shared budget/status utilities.
3. Delete `engine.py`, `step_tree.py`, and remove their exports from `context_stack/__init__.py`.
4. Re-run static guards and full Cortex tests.

## Residual Risk

- Physical deletion is not safe until the direct DFS tests are migrated/deleted. This is exactly the next cleanup work; no active behavior depends on it.
