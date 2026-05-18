# Persist Explicit Archive Diagnostics Result

## Summary

Implemented explicit runtime archive diagnostics persistence in Cortex `WakeArchived` context events.

## Changes Made

- Extended `ContextEventWriter.wake_archived(...)` to accept optional `archive_diagnostics`.
- Added `_archive_diagnostics(req)` in Cortex API and passed its output from `_append_wake_archived_event(...)`.
- Kept top-level `WakeArchived.payload.remaining_stack` unchanged as the semantic post-archive stack list used by context projection.
- Added focused Cortex test coverage proving diagnostic requests persist exact nested diagnostics while existing structural scope-end tests remain unchanged.

## Evidence

- `novaic-cortex`: `python3 -m py_compile novaic_cortex/api.py novaic_cortex/context_event_writer.py`
- `novaic-cortex`: `PYTHONPATH=.:../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_context_event_api_lifecycle.py tests/test_context_event_api_skill_lifecycle.py tests/test_context_event_write_authority.py tests/test_pr74_scope_summary_contract.py tests/test_context_event_projection.py tests/test_context_event_model.py` -> 80 passed.
- Residue scan confirmed `archive_diagnostics` is nested and `context_event_projection.py` still consumes only top-level list-shaped `remaining_stack`.

## Residual Note

This ticket persists diagnostics in Cortex context events. Aggregate runtime-to-Cortex verification remains in sibling P377.
