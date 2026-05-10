# Context append and batch event cutover completed

## Summary

P025 completed context append/batch event cutover. The request contract now supports explicit optional event idempotency keys, endpoints append ordered ContextEvents before transitional `context.jsonl` writes, and audit confirmed remaining legacy context file references are owned by Phase 4/5.

## Done

- P032 / R024:
  - Added optional `event_idempotency_key` to `ContextAppendRequest`.
  - Added optional `event_idempotency_keys` to `ContextBatchRequest`.
  - Verified same content stays distinct without keys and dedupes with explicit keys.
- P033 / R025:
  - Wired `context_append` to event writes.
  - Wired `context_batch` to ordered event writes.
  - Classified assistant messages with tool calls as `AssistantToolCallRecorded`.
- P034 / R026:
  - Audited endpoint wiring and remaining legacy references.

## Verification

- Focused append/batch audit: `7 passed in 0.28s`.
- Full Cortex suite: `442 passed in 0.80s`.

## Known Gaps

- Callers need to supply idempotency keys for transport-retry dedupe.
- Legacy `context.jsonl` cleanup/read cutover remains Phase 4/5.
- Tool step and skill lifecycle event cutovers remain P026/P027.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_contract.py`
- `novaic-cortex/tests/test_context_event_api_context_writes.py`
- `novaic-cortex/tests/test_context_event_writer.py`
