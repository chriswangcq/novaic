# Projection boundary routing result

## Summary

Phase 3.6.1 was completed as a bounded projection-boundary demotion. Active event-wired Cortex API endpoints now call projection-named Workspace methods for transitional filesystem materialization after appending ContextEvent records.

## Done

- Added projection-named Workspace methods for root/child scope lifecycle, context append, context batch append, input-message projection append, and tool-step write materialization.
- Routed event-wired API endpoints through those projection methods:
  - `/v1/scope/create`
  - `/v1/scope/end`
  - `/v1/context/append`
  - `/v1/context/batch`
  - `/v1/context/skill_begin`
  - `/v1/context/skill_end`
  - `/v1/scope/append_input`
  - `/v1/steps/write`
- Updated auto-close child materialization to call the child-close projection wrapper.
- Verified static scan no longer finds active API calls to the generic Workspace write names covered by this ticket.

## Verification

- `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_api_context_writes.py tests/test_context_event_api_steps_write.py tests/test_context_event_api_skill_lifecycle.py tests/test_context_event_api_lifecycle.py -q`
  - Result: `15 passed in 0.42s`
- `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q`
  - Result: `444 passed in 0.67s`
- Static scan:
  - `rg -n "await ws\\.(append_context|append_context_batch|write_step|complete_child_scope|archive_root_scope|append_input_message_ids|create_scope)\\(" novaic_cortex/api.py`
  - Result: no matches.

## Known Gaps

- Projection methods still delegate to the old generic Workspace implementation methods. This is intentional for Phase 3.6.1 because read-side consumers still need the materialized files.
- Broader legacy structural bypass cleanup remains for later Phase 3.6 tickets, especially runtime-level direct scope lifecycle helpers and write-authority tests.

## Artifacts

- Changed: `novaic-cortex/novaic_cortex/workspace.py`
- Changed: `novaic-cortex/novaic_cortex/api.py`
