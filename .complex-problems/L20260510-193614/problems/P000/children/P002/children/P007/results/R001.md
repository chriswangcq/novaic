# Phase 1A Result

## Summary

Implemented and tested the Cortex operational SQLite substrate module.

## Done

Changed files:

- `novaic-cortex/novaic_cortex/operational_store.py`
- `novaic-cortex/tests/test_operational_store.py`

What was delivered:

- Added `OperationalSqliteStore` with explicit filesystem SQLite path, injected `clock_ms`, and injected `id_provider`.
- Added schema initialization for:
  - `cortex_operational_meta`
  - `scope_events`
  - `scope_projection`
  - `active_stack_projection`
  - `payload_manifest`
- Implemented scope event append/list with idempotency-key retry semantics and conflict detection.
- Implemented scope projection upsert/read.
- Implemented active stack projection set/read.
- Implemented payload manifest put/read storing metadata/blob refs only.
- Removed hidden UUID generation from the factory so the ID provider is explicit.
- Fixed schema initialization to commit the meta row.

## Evidence

- `PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_operational_store.py`
  - Result: `6 passed in 0.12s`
- Hidden-input search:
  - `rg -n "time\\.time|uuid\\.uuid4|os\\.environ|:memory:" novaic-cortex/novaic_cortex/operational_store.py novaic-cortex/tests/test_operational_store.py`
  - Result: only the intentional `:memory:` rejection code and its test remain.

## Verification

- Direct unit tests passed: `6 passed in 0.12s`.
- Syntax/import path was exercised by importing `OperationalSqliteStore` and `OperationalSqliteStoreConfig`.
- Explicit dependency boundary search found no hidden `time.time`, `uuid.uuid4`, or `os.environ` use in the module.

## Known Gaps

- The store is not yet wired into Cortex startup or `WorkspaceRegistry`; that is intentionally owned by `P008`.

## Artifacts

- `novaic-cortex/novaic_cortex/operational_store.py`
- `novaic-cortex/tests/test_operational_store.py`

## Notes

This child problem did not wire the store into Cortex startup; that is owned by `P008`.
