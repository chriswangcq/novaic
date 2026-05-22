# Port Session Rebuild And Read Models To Postgres

## Problem Definition

`session_rebuild.py` reads active saga rows and projects `tq_session_state` during Queue Service startup, but the query currently has no deterministic ordering and no Postgres-specific row lock/advisory lock story. `P082` requires rebuild/read-model behavior to be explicitly Postgres-safe.

## Proposed Solution

Add a narrow Postgres dialect boundary to session rebuild:

1. Add a backend helper for the active saga context query.
2. Use deterministic ordering for both SQLite and Postgres rebuild reads.
3. Add `FOR UPDATE OF ss SKIP LOCKED` for Postgres active saga state rows while rebuild runs inside a transaction.
4. Use a Postgres-only `session_rebuild` transaction lock type; keep SQLite on its existing `global` lock type so local tests remain compatible with the lock manager.
5. Add focused tests for SQL shape, native JSON context handling, deterministic ordering, and existing rebuild behavior.

## Acceptance Criteria

- Rebuild active saga query uses deterministic ordering.
- Postgres rebuild query includes `FOR UPDATE OF ss SKIP LOCKED` and does not use SQLite JSON functions.
- Rebuild transaction uses a Postgres-specific startup lock and SQLite-compatible fallback.
- Rebuild still marks stale active sessions no-active and reconstructs active sessions from running/launched saga state.
- Tests cover Postgres SQL shape and existing SQLite rebuild behavior.

## Verification Plan

- Add focused tests for `_active_saga_contexts_sql(...)` and `_session_rebuild_lock_type(...)`.
- Run session rebuild projector tests, session state SSOT tests, queue Postgres boundary tests, session locking tests, and compile checks.

## Risks

- `SKIP LOCKED` during rebuild could skip rows if rebuild races live saga mutation. Startup should still run before accepting traffic; the lock helper documents and narrows this boundary.
- Over-expanding rebuild into live reconciliation is out of scope for this follow-up.

## Assumptions

- Rebuild is still a startup projector, not a continuously running reconciler.
- Existing `SessionLedgerRepository` remains the write boundary for rebuilt session state.
