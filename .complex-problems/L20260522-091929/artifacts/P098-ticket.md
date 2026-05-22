# Isolate Worker Startup And Recovery SQLite Compatibility Boundaries

## Problem Definition

P083's route cleanup exposed remaining SQLite vocabulary in two production-facing Queue areas: worker startup retries still directly import/catch `sqlite3.OperationalError`, and queue/saga recovery transactions still pass raw `sqlite_busy_timeout_ms=250` kwargs from unbranched repository code. This keeps the Postgres runtime path harder to reason about and weakens static cleanup guarantees.

## Proposed Solution

1. Reuse the queue transient classifier for worker startup DB connection retry:
   - remove direct `sqlite3` import/catch from `task_queue/workers/assembly_factories.py`;
   - catch general exceptions only around `db.connect(...)`;
   - retry only when `classify_queue_transient_error(...)` returns a reason and attempts remain;
   - include the low-cardinality reason in startup retry output.
2. Add a named SQLite compatibility helper for transaction timeout kwargs, preferably under `queue_service/db/`, that returns `{"sqlite_busy_timeout_ms": 250}` only for SQLite backend objects and `{}` for Postgres.
3. Replace unbranched raw timeout kwargs in `queue_db.py` and `saga_repo.py` with that helper.
4. Rewrite tests that assert raw `sqlite_busy_timeout_ms=250` counts to assert helper-boundary behavior instead.
5. Add static guards so worker assembly and repository production paths cannot reintroduce direct `sqlite3.OperationalError`, raw `sqlite_busy_timeout_ms`, or `reason=sqlite_busy` outside the explicit compatibility modules/tests.

## Acceptance Criteria

- `task_queue/workers/assembly_factories.py` has no `import sqlite3` or `sqlite3.OperationalError` token.
- Worker startup retry still retries SQLite locked/busy failures and still raises non-transient startup failures.
- Queue/saga recovery transaction call sites no longer contain the raw `sqlite_busy_timeout_ms` kwarg.
- The raw `sqlite_busy_timeout_ms` literal is isolated to a named SQLite compatibility helper and the Postgres adapter's ignore/normalization boundary if still needed.
- Existing startup retry, recovery defer, Queue Postgres boundary, and SQLite compatibility tests pass.

## Verification Plan

- Update `tests/test_pr339_worker_startup_db_retry.py` for classifier-driven retry output and non-transient behavior.
- Update `tests/test_pr345_recovery_background_defer.py` to assert helper-boundary use instead of raw timeout hint counts.
- Add/extend a static guard test over `assembly_factories.py`, `queue_db.py`, `saga_repo.py`, and the new SQLite compatibility helper.
- Run the focused P083/P098 suites, Queue Postgres boundary tests, recovery tests, and compile checks.

## Risks

- Broad exception catching in worker startup must remain scoped to the `db.connect(...)` call and immediately re-raise unknown errors.
- If a fake DB in tests lacks `backend_name`, the compatibility helper should preserve current SQLite-default local behavior.

## Assumptions

- Backend objects expose `backend_name="postgres"` for Postgres and omit it or use SQLite defaults for local SQLite fixtures.
- SQLite compatibility is allowed when it is named, isolated, and covered by tests; it should not leak into production-facing repository call sites.
