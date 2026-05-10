# DFS read fallback audit completed

## Summary

Audited and guarded the remaining DFS/context materialized read usage after the prepare/status cutover. Active API LLM read paths now have static guard tests preventing `ContextEngine` or DFS fallback from returning silently.

## Done

- Added `test_context_event_read_source_guards.py` to assert:
  - `prepare_for_llm` uses `ContextEventReadModel` and no DFS fallback symbols.
  - `context_status(include_usage=True)` uses `ContextEventReadModel` and no DFS fallback symbols.
  - `_collect_active_stack` remains only in the default status operational path.
- Removed unused `_stack_scope_ids`.
- Updated misleading comments/docstrings:
  - `context_stack` package is now labeled legacy/debug DFS utilities.
  - `ContextEngine` docstring now says active API preparation is event-projection backed.
  - Budget mapping/docs no longer imply ContextEngine-only usage.
  - Legacy DFS tests are explicitly labeled as legacy/debug coverage.
- Static audit classification:
  - Active API prepare/status usage: no DFS fallback.
  - `context_read`: materialized inspection endpoint only, not LLM read source.
  - `workspace.read_context` / context projection writes: projection artifact support.
  - `context_stack.engine` / `step_tree`: legacy/debug renderer.
  - `_collect_active_stack`: operational LIFO/status/error control path.

## Verification

- Focused legacy/guard tests: `29 passed`.
- Full Cortex suite: `452 passed`.
- Static section scan:
  - prepare: `ContextEngine=False`, `prepare_messages_for_llm=False`, `read_context=False`, `StepTree=False`, `_collect_active_stack=False`, `ContextEventReadModel=True`.
  - status: `ContextEngine=False`, `prepare_messages_for_llm=False`, `read_context=False`, `StepTree=False`, `ContextEventReadModel=True`; `_collect_active_stack=True` only for default operational stack path.

## Residual Risk

- DFS engine files still physically exist as legacy/debug code. They are no longer active API read source, but Phase 5 should decide whether to delete them outright once all legacy tests are migrated or removed.
