# Queue Postgres Boundary Implemented

## Summary

Implemented the Queue Service Postgres schema and database boundary as a bounded P073 execution. The work adds explicit sqlite/postgres backend selection, a Queue-specific Postgres adapter, a full Queue Postgres schema baseline, safe health/readiness backend reporting, and focused unit coverage. Repository SQL porting, data migration, staging validation, and production cutover remain intentionally out of scope for later child tickets.

## Done

- Added `QueuePostgresDatabase` with DSN and DSN-file support, psycopg-safe qmark placeholder conversion, literal percent escaping, SQLite-like row access, transaction helpers, and Postgres advisory locks for existing lock types.
- Added Queue database factory/public-info helpers so sqlite remains the default while postgres can be selected without exposing direct DSNs.
- Added `POSTGRES_SCHEMA_STATEMENTS`, `POSTGRES_SCHEMA_SQL`, `QUEUE_TABLES`, and `init_postgres_schema` for config plus all active `tq_*` tables.
- Represented JSON-bearing Queue columns as `jsonb` and Queue timestamp columns as `timestamptz`.
- Wired Queue Service startup through `--db-backend`, `--postgres-dsn`, and `--postgres-dsn-file`, backed by `NOVAIC_QUEUE_*` environment variables.
- Updated Queue health/root/readiness payloads to report selected backend and safe path/source details without printing raw DSNs.
- Added `psycopg[binary,pool]>=3.2` to the agent runtime requirements.
- Added focused tests for schema coverage, DSN/DSN-file behavior, placeholder conversion, transaction/advisory-lock behavior, public info secrecy, and sqlite default compatibility.

## Verification

- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_boundary.py tests/test_queue_explicit_dependencies.py tests/test_pr344_queue_claim_busy_handling.py tests/test_pr305_task_fsm_store_ledger.py tests/test_pr309_saga_fsm_store_ledger.py tests/test_pr313_worker_lease_ledger.py tests/test_pr235_session_ledger.py tests/test_pr315_queue_fsm_final_residue_guard.py` -> 34 passed.
- `PYTHONPATH=.:../novaic-common python -m pytest tests/test_queue_postgres_boundary.py` -> 10 passed after the final adapter cleanup patch.
- `PYTHONPATH=.:../novaic-common python main_novaic.py queue-service --help` -> Queue Service CLI exposes backend and Postgres DSN-file options.
- `PYTHONPATH=.:../novaic-common python -m compileall queue_service/db/postgres.py queue_service/db/__init__.py queue_service/db/schema.py queue_service/main.py main_novaic.py` -> compileall succeeded.
- `git -C novaic-agent-runtime diff --check -- queue_service/db/postgres.py queue_service/db/__init__.py queue_service/db/schema.py queue_service/main.py main_novaic.py requirements.txt tests/test_queue_postgres_boundary.py` -> no whitespace errors.

## Known Gaps

- Queue repositories still contain SQLite-specific operational SQL such as `datetime()`, `json_each()`, and JSON extraction; that belongs to P074.
- No real Postgres service was used in this boundary ticket; tests use fake pool/connection objects for unit-level boundary validation.
- No Queue data migration, staging validation, production cutover, or SQLite residue cleanup was attempted here; those remain P075-P077.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/queue-postgres-boundary-report.json`
- `novaic-agent-runtime/queue_service/db/postgres.py`
- `novaic-agent-runtime/tests/test_queue_postgres_boundary.py`
