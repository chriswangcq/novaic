# Context message idempotency contract completed

## Summary

Added an explicit optional event idempotency contract for context append/batch requests and verified that writer/store behavior keeps repeated identical messages distinct unless a caller supplies the same explicit key.

## Done

- Added `event_idempotency_key` to `ContextAppendRequest`.
- Added `event_idempotency_keys` to `ContextBatchRequest`.
- Added Pydantic validation that batch idempotency key count must match message count.
- Added tests for request contract behavior.
- Added writer tests proving:
  - same content without keys creates distinct events;
  - same explicit key dedupes retry.

## Verification

- Focused contract/writer tests:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_api_contract.py tests/test_context_event_writer.py -q`
  - Result: `10 passed in 0.28s`
- Full Cortex suite:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q`
  - Result: `438 passed in 0.74s`

## Residual Risk

- Endpoint event wiring remains open in P033.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_contract.py`
- `novaic-cortex/tests/test_context_event_writer.py`
