# ContextEvent idempotency result

## Summary

Implemented retry-safe idempotency for ContextEvent append. Repeating the same idempotency key with the same canonical semantic body returns the existing event without appending or consuming providers; reusing the key for different facts raises a conflict.

## Done

- Added `ContextEventIdempotencyConflict`.
- Updated `ContextEventStore.append_event`:
  - checks existing stream events before generated id/time provider use;
  - returns existing event for duplicate same-key same-body append;
  - raises conflict for same-key different-body append;
  - preserves explicit non-idempotent append behavior when no key is supplied.
- Confirmed `initialize_root` is retry-safe via stable `context-root:init:<stream_id>` idempotency key.
- Added focused tests for duplicate reuse, conflict, provider non-consumption, non-idempotent append, and root initialization retry.

## Verification

- `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_model.py tests/test_context_event_store.py -q` passed: 41 passed.
- `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_workspace.py::test_workspace_uses_injected_dependencies_instead_of_env tests/test_context_event_model.py tests/test_context_event_store.py -q` passed: 42 passed.
- Static scan found no hidden `uuid`, `time.`, `os.environ`, `context.jsonl`, `summary.md`, or `steps/_index` in event model/store modules.

## Known Gaps

- None for P009.
- Endpoint cutover remains tracked by later phases.

## Artifacts

- `novaic-cortex/novaic_cortex/context_event_store.py`
- `novaic-cortex/tests/test_context_event_store.py`
