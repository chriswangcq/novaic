# Check: Persist Explicit Archive Diagnostics

## Summary

Success. R356 solves P376: explicit runtime archive diagnostics are now persisted as nested `archive_diagnostics` on `WakeArchived` events, while the top-level semantic `remaining_stack` remains unchanged for context projection.

## Evidence

- R356 records the implementation and verification.
- Focused Cortex tests passed: `80 passed`.
- Compile check passed for `novaic_cortex/api.py` and `novaic_cortex/context_event_writer.py`.
- Source scan shows `context_event_projection.py` still consumes top-level `remaining_stack`, and diagnostics are nested under `archive_diagnostics`.

## Criteria Map

- Diagnostic `ScopeEndRequest` persists exact nested diagnostics: satisfied by new `test_scope_end_persists_explicit_archive_diagnostics`.
- Existing structural tests remain unchanged: satisfied by passing context event lifecycle/write authority/projection tests.
- Invalid diagnostic request validation still prevents metadata persistence: satisfied by existing `ScopeEndRequest` validation tests.
- Focused Cortex tests pass: satisfied.

## Execution Map

Implemented the persistence change in `ContextEventWriter.wake_archived(...)` and `_append_wake_archived_event(...)`, then verified with focused Cortex suites.

## Stress Test

The likely regression was corrupting context projection by changing top-level `remaining_stack` from list to dict. The implementation avoids that by adding only nested `archive_diagnostics`, and projection tests were included in the verification run.

## Residual Risk

Aggregate runtime-to-Cortex verification remains in P377.

## Result IDs

- R356
