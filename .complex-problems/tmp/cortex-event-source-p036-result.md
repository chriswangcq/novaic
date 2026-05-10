# Wire steps/write to ToolStepRecorded events result

## Summary

Implemented the `/v1/steps/write` write-side cutover to append `ToolStepRecorded` events for the resolved active scope while preserving transitional legacy step files.

## Done

- Updated `steps_write` to:
  - resolve the deepest active scope;
  - call `Workspace.normalize_step` before event emission;
  - append `ToolStepRecorded` with target scope id, call id, tool name, status, observation, and final payload ref when present;
  - write the normalized step to the existing `steps/*.json` and `_index.jsonl` projection.
- Updated `ContextEventWriter.tool_step_recorded` so payload-less tool steps do not need fake `payload_ref` values.
- Added optional tool-step idempotency handling that includes scope id for known call ids and avoids forcing a key for `unknown`.
- Added focused API tests for:
  - payload-less step events without fake payload refs;
  - deepest active child-scope targeting;
  - final blob-ref payload normalization appearing in both event and legacy step file.

## Evidence

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/context_event_writer.py`
- `novaic-cortex/tests/test_context_event_api_steps_write.py`
- Focused tests: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_api_steps_write.py tests/test_context_event_writer.py tests/test_step_index_outcome.py -q` → `23 passed`
- Full suite: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q` → `445 passed`

## Residual Risk

- Legacy step files are still written as transitional projections; P037 should audit the boundary and P028/P005 should decide when legacy writes/readers can be demoted or removed.
- Payload externalization still occurs before event append, matching the existing write ordering.
