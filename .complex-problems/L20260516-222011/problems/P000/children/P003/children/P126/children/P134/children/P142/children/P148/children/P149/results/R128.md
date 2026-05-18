# Cortex API step projection boundary result

## Summary

The active Cortex `/v1/steps/write` path normalizes requests, emits `ToolStepRecorded`, and writes through `write_step_projection`. I added API-level coverage for inline result rejection and artifact/duration metadata propagation into the step index.

## Done

- Mapped API request model at `novaic-cortex/novaic_cortex/api.py:1508-1510`.
- Mapped `steps_write` handler at `novaic-cortex/novaic_cortex/api.py:1526-1570`.
- Confirmed handler calls `ws.normalize_step(...)` before event/projection writes.
- Confirmed handler calls `ws.write_step_projection(active_path, normalized_step)`.
- Added `test_steps_write_rejects_inline_result_request`.
- Extended API valid-path test to assert `duration_ms=0` and observation artifact marker reach `_index.jsonl`.

## Verification

- Ran `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_api_steps_write.py novaic-cortex/tests/test_step_index_outcome.py`.
- Result: `28 passed in 0.44s`.

## Known Gaps

- Runtime producer shape is not judged here; it is isolated under sibling `P150`.
- Direct bypass scan is not judged here; it is isolated under sibling `P151`.

## Artifacts

- Modified `novaic-cortex/tests/test_context_event_api_steps_write.py`.
