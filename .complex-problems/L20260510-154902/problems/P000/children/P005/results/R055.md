# Phase 4 read-path cutover completed

## Summary

Completed Phase 4 by moving active LLM prepare/status usage to event projection semantics and guarding against DFS read fallback in active API paths.

## Done

- P054 built `ContextEventReadModel`, an explicit event-store/projection/budget adapter.
- P055 cut `/v1/context/prepare_for_llm` to the event adapter and added stale wake suppression semantics.
- P056 cut `context_status(include_usage=True)` to the event adapter while keeping default status as cheap operational stack inspection.
- P057 audited remaining DFS usage, added source guard tests, and relabeled DFS engine/tests as legacy/debug coverage.

## Verification

- P054 focused tests: `2 passed`; full suite: `448 passed`.
- P055 focused related tests: `33 passed`; full suite: `449 passed`.
- P056 focused status tests: `2 passed`; full suite: `450 passed`.
- P057 focused guard/legacy tests: `29 passed`; full suite: `452 passed`.

## Residual Risk

- The legacy DFS engine still physically exists for debug/legacy tests and projection artifact verification. It is no longer the active API LLM read source.
- Phase 5 should decide whether to delete legacy DFS modules/tests outright or keep them under an explicit debug-only namespace.
