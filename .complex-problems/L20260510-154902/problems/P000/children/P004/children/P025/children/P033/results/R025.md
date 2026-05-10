# Context append and batch endpoint event wiring completed

## Summary

Wired `/v1/context/append` and `/v1/context/batch` to append ContextEvents before their transitional legacy `context.jsonl` writes. User/system/plain assistant messages become `ContextMessageAppended`; assistant messages with tool calls become `AssistantToolCallRecorded`.

## Done

- Added `_append_context_message_event` helper in `api.py`.
- Wired `context_append` with optional `event_idempotency_key`.
- Wired `context_batch` with optional per-message `event_idempotency_keys`.
- Classified assistant messages with `tool_calls` as `AssistantToolCallRecorded`.
- Preserved legacy context writes as transitional behavior until read-path/cleanup phases.
- Added `tests/test_context_event_api_context_writes.py`.

## Verification

- Focused context API tests:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_api_context_writes.py tests/test_context_event_api_contract.py tests/test_context_event_api_lifecycle.py tests/test_pr67_wake_child_api.py -q`
  - Result: `17 passed in 0.31s`
- Full Cortex suite:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q`
  - Result: `442 passed in 0.65s`

## Residual Risk

- Existing callers that do not provide idempotency keys preserve previous retry semantics and can still append duplicate messages on transport retry; this is deliberate compatibility until callers adopt keys.
- Legacy `context.jsonl` writes remain transitional until Phase 4/5.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_context_writes.py`
