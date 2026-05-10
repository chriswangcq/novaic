# ContextEvent store read-side result

## Summary

Implemented the read/replay side of the ContextEvent store. It owns the event-log path, returns empty streams for missing logs, parses JSONL rows, validates each persisted event through the ContextEvent schema, and fails loudly on corrupt rows.

## Done

- Added `novaic-cortex/novaic_cortex/context_event_store.py`.
- Added `ContextEventStoreError`.
- Added `ContextEventStore.event_log_path(root_scope_path)`.
- Added `ContextEventStore.read_events(root_scope_path)`.
- Added focused tests in `novaic-cortex/tests/test_context_event_store.py`.

## Verification

- `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_model.py tests/test_context_event_store.py -q` passed: 32 passed.
- Static scan of `novaic_cortex/context_event_store.py` found no `uuid`, `time.`, `os.environ`, `_sys_append_line`, `_sys_write`, `context.jsonl`, `summary.md`, or `steps/_index`.
- Static scan only found `_sys_write` in tests, where it is used to seed fixture rows.

## Known Gaps

- Append/write behavior is not implemented in P012; it is tracked by P013.
- Store idempotency behavior is not implemented in P012; it is tracked by P009.

## Artifacts

- `novaic-cortex/novaic_cortex/context_event_store.py`
- `novaic-cortex/tests/test_context_event_store.py`
