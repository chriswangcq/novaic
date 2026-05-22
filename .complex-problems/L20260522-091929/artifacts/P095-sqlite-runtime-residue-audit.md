# P095 SQLite Runtime Residue Audit

## Scope

Audited Queue Service session/outbox runtime wiring and adjacent database adapter files after the Postgres cutover cleanup.

Command:

```bash
rg -n "sqlite|\\.db|\\.sqlite|DB_PATH|SQLITE_DB_PATH|NOVAIC_QUEUE_DB_BACKEND|sqlite_path|sqlite_master|sqlite3" queue_service/main.py queue_service/__init__.py queue_service/db queue_service/fsm queue_service/session_*.py queue_service/*outbox*.py queue_service/*ledger.py queue_service/saga_repo.py
```

## Removed Runtime Residue

- `queue_service/main.py` no longer defaults `NOVAIC_QUEUE_DB_BACKEND` to `sqlite`.
- `queue_service/main.py` no longer describes `$NOVAIC_DATA_DIR/queue.db` as the normal database.
- `queue_service/__init__.py` no longer describes `queue.db` as the Queue Service database.
- Generic `DB_PATH` was renamed to `SQLITE_DB_PATH` to make local SQLite path usage explicit.

## Explicit Runtime Boundary

- `queue_service/main.py` now defaults to Postgres:
  - `os.environ.get("NOVAIC_QUEUE_DB_BACKEND", "postgres")`
- `SQLITE_DB_PATH` is still passed to the database factory because the factory API supports explicit SQLite adapter mode and tests.
- `sqlite_path` appears only inside `if QUEUE_DB_BACKEND == "sqlite"` readiness output.
- `_database_label()` returns the SQLite path only when `DATABASE_PUBLIC_INFO["backend"] == "sqlite"`.

## Retained Adapter/Test/Migration Boundaries

- `queue_service/db/__init__.py`
  - Retained explicit `backend="sqlite"` adapter construction and public info.
- `queue_service/db/schema.py`
  - Retained SQLite schema baseline and `sqlite_master` checks for explicit SQLite databases.
- `queue_service/fsm/sqlite_store.py`
  - Retained SQLite adapter implementation, busy retry handling, and Postgres-vs-SQLite dialect selection.
- `queue_service/db/postgres.py`
  - Retained `sqlite_busy_timeout_ms` discard for API compatibility with existing transaction call sites.
- `queue_service/*_ledger.py`
  - Retained imports of `FsmSqliteStore` because the class remains the generic FSM store implementation name during transition.
- `tests/test_queue_postgres_boundary.py`
  - Retained explicit SQLite factory assertions as adapter boundary tests.

## Guard Tests

- `tests/test_queue_runtime_postgres_default.py`
  - Guards Postgres default backend.
  - Guards against restoring `"sqlite"` as the default backend.
  - Guards that `queue.db` is described only as explicit SQLite mode.
  - Guards that the SQLite path variable is named `SQLITE_DB_PATH` and used only under explicit SQLite branches.

## Remaining Risk

- The generic store class is still named `FsmSqliteStore`; renaming it would be a wider API cleanup and is intentionally deferred because current criteria only require runtime path isolation.
