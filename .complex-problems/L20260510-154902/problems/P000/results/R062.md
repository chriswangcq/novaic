# Cortex full event-sourced context source cutover result

## Summary

Completed the Cortex LLM context source cutover to an event-sourced model with no DFS fallback. The implementation now writes context lifecycle events, projects LLM context from those events, rejects legacy-only roots with explicit reset-required behavior, and physically removes the old DFS renderer.

## Done

- Designed and implemented context event domain, event store, writer, projection, and read model.
- Cut active write APIs to emit context events.
- Cut `prepare_for_llm` to `ContextEventReadModel`.
- Cut usage/status accounting to event projection.
- Added source guards proving active paths do not call DFS renderer symbols.
- Added no-compat reset behavior for legacy-only data.
- Removed old DFS renderer files and exports:
  - `context_stack/engine.py`
  - `context_stack/step_tree.py`
  - `ContextEngine`, `StepTree`, `StepNode`, `StepTreeBuilder`
- Deleted or migrated direct DFS renderer tests.
- Preserved shared budget/status types under `context_stack`.
- Re-ran focused and full verification.

## Evidence

Final production old-symbol scan:

```bash
rg -n "ContextEngine|StepTree|prepare_messages_for_llm|context_stack\\.engine|context_stack\\.step_tree" novaic-cortex/novaic_cortex
```

Result: no matches.

Final full Cortex test suite:

```text
430 passed
```

Final diff shape inside `novaic-cortex` after physical cleanup:

```text
791 insertions(+), 1903 deletions(-)
```

## Phases

- Phase 0: design and ledger setup.
- Phase 1: event model/store/write authority.
- Phase 2: event projection and read model.
- Phase 3: API write/read cutover.
- Phase 4: active read source cutover and DFS fallback guards.
- Phase 5: legacy cleanup, reset behavior, and full verification.

## Residual Risk

The cutover intentionally removes backward compatibility for legacy-only roots. That matches the user's instruction that old data can be deleted and the system should do a full cut. Operational reset/rebuild flows should handle old roots explicitly rather than silently reading DFS state.
