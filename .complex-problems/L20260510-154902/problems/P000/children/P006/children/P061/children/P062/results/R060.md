# Legacy DFS renderer physical deletion result

## Summary

Physically removed the legacy DFS renderer from the active Cortex package and migrated/deleted the remaining direct test surface. Event projection now owns the wake summary folding and system-message ordering semantics that the old renderer previously covered.

## Done

- Deleted `novaic_cortex/context_stack/engine.py`.
- Deleted `novaic_cortex/context_stack/step_tree.py`.
- Removed `ContextEngine`, `StepTree`, `StepNode`, and `StepTreeBuilder` exports from `context_stack/__init__.py`.
- Deleted direct legacy DFS tests:
  - `tests/test_context_engine_dfs.py`
  - `tests/test_pr66_system_scope_rendering.py`
  - `tests/test_pr73_folded_scope_rendering.py`
- Migrated `tests/test_pr84_minimal_structure_invariants.py` from direct `ContextEngine` rendering to event-written API context plus `context_prepare_for_llm`.
- Updated `tests/test_pr67_wake_child_api.py` so the default status test guards against accidental event read-model rendering, instead of monkeypatching the removed DFS renderer.
- Extended `context_event_projection.py` to close active wake scopes by replacing wake-local raw messages with the persisted wake summary.
- Extended `context_event_projection.py` to keep explicit system prompt messages ahead of summaries/current user content.

## Evidence

Focused tests:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-cortex/tests/test_pr67_wake_child_api.py \
  novaic-cortex/tests/test_pr84_minimal_structure_invariants.py \
  novaic-cortex/tests/test_context_event_read_source_guards.py \
  novaic-cortex/tests/test_context_event_projection.py \
  novaic-cortex/tests/test_context_event_read_model.py
```

Result:

```text
41 passed
```

Full Cortex suite:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests
```

Result:

```text
430 passed
```

Production legacy symbol scan:

```bash
rg -n "ContextEngine|StepTree|prepare_messages_for_llm|context_stack\\.engine|context_stack\\.step_tree" novaic-cortex/novaic_cortex
```

Result: no matches.

Remaining context stack package files:

```text
novaic-cortex/novaic_cortex/context_stack/__init__.py
novaic-cortex/novaic_cortex/context_stack/budget.py
novaic-cortex/novaic_cortex/context_stack/types.py
```

## Notes

The total test count dropped from 455 to 430 because direct legacy DFS renderer tests were deleted. The active package no longer exposes the old renderer symbols; remaining test-string mentions are source-guard assertions only.
