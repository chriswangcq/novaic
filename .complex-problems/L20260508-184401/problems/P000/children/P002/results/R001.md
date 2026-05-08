# Result summary

## Summary

Added and ran targeted regression tests for the production failure modes: DispatchAssembler timeout configuration, generic FSM SQLite busy retry, and queue claim endpoint busy handling.

## Done

- Added `test_dispatch_sync_client_uses_configured_http_timeout` to `novaic-common/tests/test_assembler_sync.py`.
- Added `test_generic_fsm_store_retries_transient_sqlite_busy` to `novaic-agent-runtime/tests/test_pr259_generic_fsm_store_outbox.py`.
- Added `novaic-agent-runtime/tests/test_pr344_queue_claim_busy_handling.py`.
  - Verifies `/tasks/claim` returns `{"task": None}` on transient SQLite busy.
  - Verifies `/sagas/claim` returns `{"saga": None}` on transient SQLite busy.

## Verification

- Ran `PYTHONPATH=. pytest -q tests/test_assembler_sync.py` in `novaic-common`: 16 passed.
- Ran `PYTHONPATH=. pytest -q tests/test_pr259_generic_fsm_store_outbox.py tests/test_pr344_queue_claim_busy_handling.py` in `novaic-agent-runtime`: 6 passed.

## Known Gaps

- Production deployment and smoke are still pending in P003.

## Artifacts

- `novaic-common/tests/test_assembler_sync.py`
- `novaic-agent-runtime/tests/test_pr259_generic_fsm_store_outbox.py`
- `novaic-agent-runtime/tests/test_pr344_queue_claim_busy_handling.py`
