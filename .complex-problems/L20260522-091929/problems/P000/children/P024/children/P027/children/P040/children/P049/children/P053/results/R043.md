# Entangled Migration Planner And Report Model Result

## Summary

`T047` implemented the first offline migration layer for Entangled: a side-effect-light planner/report module that inspects SQLite read-only, classifies tables, plans `rowid` preservation, guards target cleanup, plans identity resets, and renders redacted report dictionaries. No production or Postgres target was touched.

## Done

- Added `Entangled/packages/server-python/entangled/sql/migration.py`.
- Added read-only SQLite URI connection helpers and source inventory inspection.
- Added table inventory, copy plan, sequence reset plan, migration plan, skipped table, and report data models.
- Added table classification for dynamic entity tables, `entangled_sync_versions`, `subagent_state_transitions`, SQLite internal tables, and ignored underscore-prefixed tables.
- Added dynamic-table `rowid` to Postgres `entangled_rowid` copy planning.
- Added sequence reset planning for dynamic `entangled_rowid`, integer `id` columns, and transition IDs.
- Added target cleanup confirmation guard.
- Added secret redaction for DSN userinfo and common password/token key-value forms.
- Added focused tests in `Entangled/packages/server-python/tests/test_migration_planner.py`.

## Verification

- `python -m pytest tests/test_migration_planner.py`: 7 passed.
- `python -m py_compile entangled/sql/migration.py`: passed.
- `python -m pytest`: 112 passed.

## Known Gaps

- This ticket does not execute data copy into Postgres; that remains assigned to the copy-executor child.
- This ticket does not expose a CLI; that remains assigned to the CLI/tests child.
- Planner table classification is intentionally conservative and can be tightened after staging inventory validation.

## Artifacts

- `Entangled/packages/server-python/entangled/sql/migration.py`
- `Entangled/packages/server-python/tests/test_migration_planner.py`
