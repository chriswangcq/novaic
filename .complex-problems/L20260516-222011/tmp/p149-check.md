# Cortex API step projection success check

## Summary

Success. `R128` proves the active Cortex API endpoint enforces the structured step contract and writes valid requests through the projection boundary into durable step/index records.

## Evidence

- Request model: `novaic-cortex/novaic_cortex/api.py:1508-1510`.
- Handler normalization and event/projection writes: `novaic-cortex/novaic_cortex/api.py:1526-1570`.
- API inline-result rejection test: `test_steps_write_rejects_inline_result_request`.
- API valid-path index metadata assertions: `test_steps_write_emits_tool_step_recorded_without_fake_payload_ref`.
- Blob payload API path assertions: `test_steps_write_records_deepest_scope_and_final_blob_payload_ref`.
- Verification: `28 passed in 0.44s`.

## Criteria Map

- API model and handler mapped: satisfied.
- Handler calls strict boundary: satisfied by `normalize_step` and `write_step_projection` source pointers.
- Inline `result` rejected through API: satisfied by new API test.
- Valid request writes step/index refs and metadata: satisfied by existing blob test plus extended artifact/duration index assertions.

## Execution Map

- Result `R128` inspected the endpoint, added missing API-level rejection coverage, extended active-path metadata coverage, and reran API plus workspace step tests.

## Stress Test

- The API rejection test sends the exact stale shape we want to eliminate: a tool step with inline `result` and no observation.
- The valid-path test sends observation-level artifacts and zero duration to verify metadata survives the endpoint boundary, not just the workspace helper.

## Residual Risk

- Non-blocking for `P149`: runtime producer and bypass scans remain as sibling problems and are not claimed solved here.

## Result IDs

- `R128`
