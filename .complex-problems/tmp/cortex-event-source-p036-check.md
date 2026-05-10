# P036 success check

## Summary

Success. R029 closes P036: `/v1/steps/write` now emits `ToolStepRecorded` events for the resolved deepest active scope and preserves the legacy step-file projection during the transitional phase.

## Evidence

- R029 changed `novaic-cortex/novaic_cortex/api.py` so `steps_write` normalizes the step, emits `ToolStepRecorded`, and then writes the normalized legacy step file.
- R029 changed `novaic-cortex/novaic_cortex/context_event_writer.py` so `payload_ref` is optional and no fake ref is required for payload-less steps.
- R029 added `novaic-cortex/tests/test_context_event_api_steps_write.py`.
- Focused verification passed: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_api_steps_write.py tests/test_context_event_writer.py tests/test_step_index_outcome.py -q` → `23 passed`.
- Full verification passed: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q` → `445 passed`.

## Criteria Map

- `steps_write` appends `ToolStepRecorded` with target scope id: met; tests assert event payload uses `wake-1` and child `skill-1`.
- Event payload preserves call id, tool name, status, observation, and final payload ref: met; focused tests assert exact event payloads, including final `blob://cortex-payload/blob-1`.
- Legacy step files remain transitional: met; tests read `_index.jsonl` and written `steps/*.json`.
- Focused tests verify event stream rows: met through `ContextEventStore.read_events` assertions.

## Execution Map

- P036 ticket T032 executed in R029.
- The implementation depends on P035 normalization and does not perform read-path cutover or legacy deletion.
- P037 remains responsible for a broader audit of tool-step cutover boundaries.

## Stress Test

- Tested no-payload tool results to prevent fake payload refs.
- Tested payload-bearing tool results with blob externalization so event and file projection agree on the final ref.
- Tested deepest active child scope resolution because that is the easy place for event target drift.
- Ran the full Cortex suite after focused tests.

## Residual Risk

- Transitional duplicate writes remain by design: event stream plus legacy step files.
- Payload write happens before event append; this is inherited from the existing payload externalization order and should be revisited only with a transaction/outbox layer.

## Result IDs

- R029
