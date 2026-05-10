# Projection boundary routing check

## Summary

Success. Result R037 satisfies P042: active event-wired API endpoints now use projection-named Workspace methods for transitional filesystem writes, while behavior remains covered by focused and full tests.

## Evidence

- Static scan for direct active API calls to generic write methods returned no matches:
  - `rg -n "await ws\\.(append_context|append_context_batch|write_step|complete_child_scope|archive_root_scope|append_input_message_ids|create_scope)\\(" novaic-cortex/novaic_cortex/api.py`
- Projection methods and call sites are present in:
  - `novaic-cortex/novaic_cortex/workspace.py`
  - `novaic-cortex/novaic_cortex/api.py`
- Focused event API tests passed:
  - `15 passed in 0.42s`
- Full Cortex suite passed:
  - `444 passed in 0.67s`

## Criteria Map

- `context_append` / `context_batch` use context projection methods: satisfied by `append_context_projection` and `append_context_batch_projection` call sites.
- `steps_write` uses step projection method: satisfied by `write_step_projection`.
- `context_skill_end` uses skill close projection method: satisfied by `complete_child_scope_projection`.
- Existing tests continue to pass: satisfied by the full `444 passed` suite.
- Static scans can distinguish active event append calls from projection writes: satisfied by no generic write calls in active API scan and explicit projection call sites.

## Execution Map

- R037 added projection wrappers in Workspace.
- R037 routed event-wired API endpoints through those wrappers.
- R037 verified no behavior regression with focused and full test suites.

## Stress Test

- The check looked for generic Workspace write calls in `api.py` after the routing change, because that is where accidental reattachment to legacy source-like writes would show up first.
- The full test suite gives broad regression coverage across existing Cortex behavior while focused tests cover event write endpoints directly.

## Residual Risk

- Projection wrappers still delegate to generic Workspace methods internally. That is acceptable for this phase because the ticket’s scope is API demotion/naming isolation, not read-side projection deletion.
- Remaining legacy write-path cleanup is intentionally tracked in subsequent Phase 3.6 tickets.

## Result IDs

- R037
