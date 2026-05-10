# ContextEvent append/root initialization result

## Summary

Implemented the append/write side of the ContextEvent store. Append now assigns generated event fields from explicit providers, computes monotonic per-stream sequence from existing events, validates the event envelope, and persists exactly one JSONL row. Fresh root initialization appends `RootInitialized` without legacy DFS migration.

## Done

- Extended `novaic-cortex/novaic_cortex/context_event_store.py`:
  - injected `clock` and `id_provider`;
  - `append_event`;
  - `initialize_root`.
- Added tests in `novaic-cortex/tests/test_context_event_store.py` for:
  - append requiring explicit providers;
  - injected event id and occurred_at;
  - monotonic sequence;
  - stream/root mismatch rejection;
  - fresh root initialization payload and idempotency key.

## Verification

- `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_model.py tests/test_context_event_store.py -q` passed: 37 passed.
- `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_workspace.py::test_workspace_uses_injected_dependencies_instead_of_env tests/test_context_event_model.py tests/test_context_event_store.py -q` passed: 38 passed.
- Static scan found no hidden `uuid`, `time.`, `os.environ`, `context.jsonl`, `summary.md`, or `steps/_index` in the event model/store modules.
- Static scan found `_sys_append_line` only in the store append implementation and `_sys_write` only in tests for fixture seeding.

## Known Gaps

- Retry-safe idempotency dedupe/conflict behavior is not implemented here; it is tracked by P009.
- Production concurrency/serialization is not handled in the store itself; later integration should use existing Cortex mutation locks or an equivalent per-stream lock.

## Artifacts

- `novaic-cortex/novaic_cortex/context_event_store.py`
- `novaic-cortex/tests/test_context_event_store.py`
