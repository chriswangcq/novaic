# Phase 5B Remove Dead Local Authority Code Result

## Summary

Closed Phase 5B by moving scope lookup/uniqueness to SQLite projection, quarantining the remaining archive tree walk as debug/archive projection only, and removing stale compatibility wrapper surfaces. The phase also found and removed the lingering runtime/Cortex `include_display` projection selector through a follow-up gate.

## Done

- P049/R044: Scope lookup and duplicate scope-id checks now use operational SQLite `scope_projection`; old root `meta.scope_ids` registration and API tree-walk lookup were removed.
- P050/R045: `_walk_scope_tree` was removed from live source and replaced with archive-only `_build_archive_scope_index_projection`.
- P051/R051: Compatibility wrapper review/removal completed:
  - removed `format_for_llm`
  - cleaned misleading legacy wording
  - preserved negative guard tests
  - removed `include_display` from step formatting after final gate discovered it.

## Verification

- P049 targeted projection/lifecycle/API suite passed: `45 passed`; additional lifecycle/history/control suite passed: `31 passed`.
- P050 targeted source guard/scope/archive/lifecycle suite passed: `49 passed`.
- P051/P055 final verification passed:
  - no `format_for_llm` matches across Cortex and sibling packages
  - no step-formatting `include_display` matches in Cortex/runtime request/client paths
  - Cortex final targeted suite: `39 passed`
  - Runtime targeted suite: `11 passed`.
- Compile checks passed for all modified Cortex/runtime modules covered by child results.

## Known Gaps

- None for Phase 5B's source-code local authority cleanup slice.
- Phase 5C still owns current docs/comments cleanup outside this source/test compatibility slice.
- Phase 5D still owns broad static guards and full-suite verification for the whole Phase 5 cleanup.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/novaic_cortex/operational_store.py`
- `novaic-cortex/novaic_cortex/scope_state.py`
- `novaic-cortex/novaic_cortex/scope_transition_events.py`
- `novaic-cortex/novaic_cortex/step_result_projection.py`
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- Updated Cortex/runtime tests and ledger artifacts under `.complex-problems/L20260510-193614`.
