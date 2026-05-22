# Check: Session Rebuild Read Models Succeed

## Summary

`R090` solves `P097`. Session rebuild now has a backend-aware query boundary with deterministic ordering, Postgres row locking, and a Postgres-specific startup transaction lock type while keeping SQLite local behavior compatible.

## Evidence

- `session_rebuild.py` uses `_active_saga_contexts_sql(backend=...)`.
- Postgres SQL includes `ORDER BY ss.updated_at, ss.saga_id` and `FOR UPDATE OF ss SKIP LOCKED`.
- SQLite SQL keeps deterministic ordering without Postgres lock syntax.
- `_session_rebuild_lock_type(...)` selects `session_rebuild` for Postgres and `global` for SQLite.
- Rebuild projector tests and related session/Postgres tests passed.

## Criteria Map

- Inspect for SQLite-only SQL / implicit ordering: satisfied by helper tests and rg audit.
- Add Postgres-safe ordering/locking helpers: satisfied by `_active_saga_contexts_sql` and `_session_rebuild_lock_type`.
- Ensure stale active state is marked no-active and active state reconstructed: existing rebuild projector and SSOT tests still pass.
- Focused Postgres rebuild/read-model SQL tests: satisfied by added tests in `test_pr279_session_rebuild_projector_boundary.py`.
- Required regressions: targeted rebuild, session SSOT, queue Postgres boundary, session locking, and runtime default tests passed.

## Execution Map

- Result: R090.

## Stress Test

- SQL-shape tests cover the Postgres lock and deterministic ordering primitives.
- Existing rebuild behavior tests cover invalid generation filtering and positive generation projection.

## Residual Risk

- Rebuild remains a startup projector; it is not a live reconciler. That matches the problem scope.
- Full `test_pr318_projection_table_quarantine_guard.py` still has unrelated task/saga static guard failures from previous helper extraction; the rebuild-specific pr318 test passed and this does not block `P097`.

## Result IDs

- R090
