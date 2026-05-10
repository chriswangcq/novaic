# Phase 3D Quarantine File-Walk Stack Authority Parent Result

## Summary

Completed Phase 3D through five closed child problems. Live Cortex API stack authority no longer uses file-walk active-stack collection or `resolve_active_scope_path(...)`; stack reads and live active-path routing now use SQLite active-stack projection. The old `_collect_active_stack(...)` helper was physically deleted from `api.py`.

## Done

- P035/R029: cut `scope_end` archive/finalize stack snapshots to SQLite projection.
- P036/R030: cut `skill_begin` validation/duplicate/depth/success/exception stack responses and projection writes to SQLite projection.
- P037/R031: cut `skill_end` exception diagnostics to projection-derived stack data.
- P038/R032: cut `scope_write_assistant` and `steps_write` routing to SQLite projection; added `Workspace.write_assistant(...)` coverage.
- P039/R033: replaced wake creation projection seeding with deterministic frames, deleted `_collect_active_stack(...)`, and added whole-file guards.

## Verification

- Child problems P035-P039 each have successful checks C031-C035.
- Latest full Cortex suite:
  - `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests`
  - Passed: 462 tests.
- Static final audit:
  - `rg -n "_collect_active_stack|resolve_active_scope_path" novaic-cortex/novaic_cortex/api.py -S`
  - No matches.

## Boundary Decisions

- `Workspace.resolve_active_scope_path(...)` may remain below the API layer as a lower-level legacy/repair utility, but live `api.py` authority no longer calls it.
- Duplicate-ID filesystem tree walking in `skill_begin` remains only as scope-id uniqueness cross-check, not active-stack authority.
- Direct non-wake `scope_create` is no longer treated as live active-stack routing authority; runtime child skills are opened through `context_skill_begin`.

## Changed Areas

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
- `novaic-cortex/tests/test_context_event_api_steps_write.py`
- `novaic-cortex/tests/test_context_event_read_source_guards.py`
- `novaic-cortex/tests/test_pr67_wake_child_api.py`

## Residual Risk

- Parent-level P020 check still needs to validate aggregate criteria against all child results.
- Phase 3E remains responsible for a broader active-stack cutover verification gate after this cleanup.
