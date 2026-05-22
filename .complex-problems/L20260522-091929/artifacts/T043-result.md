# Entangled Postgres row output shape result

## Summary

P048 added focused row-shape regression coverage for Entangled Postgres query paths. No production code changes were required beyond the earlier serialization/deserialization logic; tests now prove native Postgres-style JSON/BOOL values and legacy SQLite-style values produce compatible API rows.

## Done

- Added fake-Postgres row-shape tests for native JSON dict/list-style values, booleans, timestamp strings, hidden fields, and `has_<hidden>` markers.
- Added legacy compatibility tests for JSON strings and integer booleans.
- Added input serialization coverage for JSON, BOOL, and hidden marker computation.
- Added list output coverage through `SqlEntityStore.list`.

## Verification

- Targeted row-shape tests passed: `13 passed`.
- Full Entangled test suite passed: `99 passed`.
- py_compile passed for touched modules.

## Known Gaps

- Real Postgres execution remains deferred to staging validation.
- Migration tooling still needs to preserve row values and copy SQLite `rowid` into `entangled_rowid`.

## Artifacts

- `Entangled/packages/server-python/tests/test_postgres_row_output_shape.py`
