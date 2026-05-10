# Context append and batch cutover audit completed

## Summary

Audited the context append/batch cutover after P032/P033. The endpoints now call the event append helper before transitional legacy writes, focused tests verify event behavior, and remaining `context.jsonl` read/write references are explicitly classified as Phase 4/5 legacy/projection work.

## Done

- Ran focused context contract/wiring tests:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_api_context_writes.py tests/test_context_event_api_contract.py -q`
  - Result: `7 passed in 0.28s`
- Ran full Cortex suite:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q`
  - Result: `442 passed in 0.80s`
- Static scan confirmed:
  - `context_append` calls `_append_context_message_event`;
  - `context_batch` calls `_append_context_message_event`;
  - remaining `context.jsonl` read/write references are in legacy `ContextEngine`, legacy append projection, overwrite helper, and archived label extraction.

## Residual Risk

- `context.jsonl` is still written as transitional output and read by legacy ContextEngine; Phase 4/5 own removing that dependency.
- No unresolved bypass was found for append/batch endpoints.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_context_writes.py`
