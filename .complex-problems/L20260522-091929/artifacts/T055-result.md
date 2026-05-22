# Entangled Postgres REST Smoke Result

## Summary

`T055` ran the REST smoke suite against the Postgres-mode Entangled staging process. The first run exposed a real Postgres write bug: BOOL input was serialized as SQLite-style `0/1`, which Postgres rejected for boolean columns. The bug was fixed by preserving Python bool values on Postgres input paths, redeployed to the API host, and the second REST smoke run passed all required operations. The staging process was stopped afterward.

## Done

- Ran health/readiness, list/read, upsert/read, append/query, patch update, CAS update, delete, and final cleanup smokes against `rest-smoke-events`.
- Fixed Postgres BOOL input serialization in `Entangled/packages/server-python/entangled/sql/entity_store.py`.
- Added local regression coverage in `Entangled/packages/server-python/tests/test_postgres_entity_write_queries.py`.
- Synced the fix to the API host staging package.
- Reran REST smokes successfully.
- Stopped the staging process and verified the report shows port `19910` no longer listening.
- Wrote `.complex-problems/L20260522-091929/artifacts/entangled-rest-smoke-report.json`.

## Verification

- First smoke failure evidence: Postgres rejected `smallint` for boolean column `is_enabled`.
- Local targeted tests after fix:
  - `python -m pytest tests/test_postgres_entity_write_queries.py tests/test_migration_semantic_validation.py`: 6 passed.
  - `python -m py_compile entangled/sql/entity_store.py`: passed.
- Local full Entangled pytest after fix: 125 passed.
- Final remote REST smoke report:
  - `all_required_ok`: true.
  - health/readiness: HTTP 200.
  - list/read fixture: HTTP 200.
  - upsert/read: HTTP 200.
  - append/query: HTTP 200.
  - patch update: HTTP 200.
  - CAS update: HTTP 200.
  - delete upserted and appended rows: HTTP 200.
  - final list returned only the original fixture row.
  - raw DSN/token recorded: false.
  - staging process stopped: true.

## Known Gaps

- WebSocket sync validation is not covered here; `P052` owns it.
- REST smoke uses a fixture schema/data set, not a full production import.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/entangled-rest-smoke-report.json`
- `Entangled/packages/server-python/entangled/sql/entity_store.py`
- `Entangled/packages/server-python/tests/test_postgres_entity_write_queries.py`
