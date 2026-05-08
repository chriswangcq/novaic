# Result summary

## Summary

Implemented the first bounded repair for the production handoff failure: DispatchAssembler now uses the configured 30 second service timeout, SQLite connections wait long enough for normal WAL writer contention, the generic FSM store retries transient SQLite busy/locked errors, and task/saga claim endpoints defer transient busy claims as empty claims instead of surfacing plaintext 500s to workers.

## Done

- Patched `novaic-common/common/wake/assembler.py`.
  - `_get_sync_client()` now passes `timeout=httpx.Timeout(ServiceConfig.HTTP_TIMEOUT, connect=10.0)` into `internal_sync_client`.
  - This removes the observed default 5 second httpx read timeout from Business subscriber dispatch.
- Patched `novaic-common/common/db/database.py`.
  - Per-connection `PRAGMA busy_timeout` changed from `3000` to `15000`.
  - This keeps transient queue-service WAL contention below the 30 second internal HTTP timeout instead of surfacing as immediate user-visible dispatch/saga failures.
- Patched `novaic-agent-runtime/queue_service/fsm/sqlite_store.py`.
  - Added bounded retry for `sqlite3.OperationalError` containing `database is locked` or `database is busy`.
  - Routed generic FSM store inserts, updates, and selects through that retry wrapper.
- Patched `novaic-agent-runtime/queue_service/routes.py`.
  - Task claim and saga claim now catch transient SQLite busy/locked errors and return an empty claim with a warning log.
  - This prevents the worker loop from receiving plaintext 500 responses and JSON parse errors for transient claim contention.

## Verification

- Ran Python compile check on changed modules:
  - `novaic-common/common/wake/assembler.py`
  - `novaic-common/common/db/database.py`
  - `novaic-agent-runtime/queue_service/fsm/sqlite_store.py`
  - `novaic-agent-runtime/queue_service/routes.py`
- Reviewed diffs for the touched files.

## Known Gaps

- Targeted tests are still required in child problem P002.
- Deployment and production smoke are still required in child problem P003.
- The patch intentionally does not redesign queue-service claim polling yet; it closes the observed production failure mode with explicit timeout, busy wait, retry, and non-500 transient claim handling.

## Artifacts

- Modified files:
  - `novaic-common/common/wake/assembler.py`
  - `novaic-common/common/db/database.py`
  - `novaic-agent-runtime/queue_service/fsm/sqlite_store.py`
  - `novaic-agent-runtime/queue_service/routes.py`
