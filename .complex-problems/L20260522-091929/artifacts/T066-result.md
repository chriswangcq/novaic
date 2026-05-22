# Fix Entangled Postgres Percent Placeholder Escaping Locally Result

## Summary

Patched the Entangled Postgres adapter so literal `%` characters are escaped for psycopg while the existing SQLite-style `?` to `%s` placeholder conversion remains intact. Added regression coverage for DDL containing `LIKE 'blob://%'` and for quoted question-mark handling.

## Done

- Updated `Entangled/packages/server-python/entangled/sql/database.py`.
- Added regression tests in `Entangled/packages/server-python/tests/test_postgres_database_boundary.py`.
- Preserved quote-aware conversion of unquoted `?` placeholders.
- Escaped literal `%` characters as `%%`, including inside quoted SQL literals where psycopg still scans placeholder syntax.

## Verification

- `python -m pytest tests/test_postgres_database_boundary.py tests/test_schema_and_notifier.py tests/test_ws_smoke_client.py` passed with `25 passed`.
- `python -m pytest` passed with `133 passed`.

## Known Gaps

- The fix is local only; it still needs to be deployed to `api.gradievo.com` and verified against production schema registration.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/entangled-placeholder-local-repair-report.json`
- `Entangled/packages/server-python/entangled/sql/database.py`
- `Entangled/packages/server-python/tests/test_postgres_database_boundary.py`
