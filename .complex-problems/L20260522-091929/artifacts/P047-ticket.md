# Port Entangled stream rowid semantics to Postgres

## Problem Definition

Entangled stream pagination and cleanup use SQLite `rowid` as a stable tie-breaker when cursor field values collide. Postgres dynamic tables now have `entangled_rowid`, but `SqlEntityStore` still emits `rowid` in list_stream, exists_before, and cleanup/default ordering paths.

## Proposed Solution

1. Add `SqlEntityStore` helpers for backend-specific internal rowid/tie-break columns.
2. Replace hard-coded `rowid` in stream cursor lookup and pagination predicates with the helper.
3. Replace default cleanup/list ordering fallback from `rowid DESC` to the backend-specific internal rowid expression.
4. Update validation so the backend-specific internal tie-break column is allowed safely.
5. Add tests for SQLite `rowid` behavior and Postgres `entangled_rowid` query generation with duplicate cursor semantics.
6. Run full Entangled tests.

## Acceptance Criteria

- Postgres `list_stream` SQL selects `entangled_rowid AS _rid`.
- Postgres pagination predicates compare `entangled_rowid` instead of `rowid`.
- Postgres cleanup/default ordering uses `entangled_rowid DESC`.
- SQLite paths still use `rowid`.
- Validation permits the correct internal tie-break key and rejects unknown fields.
- Focused tests and full Entangled tests pass.

## Verification Plan

Use fake Postgres SQL-capture tests for list_stream, exists_before, and cleanup query generation. Run full Entangled pytest and py_compile. Do not run production cutover in this child.

## Risks

- Missing one rowid occurrence can create subtle stream pagination divergence.
- Allowing internal columns in validation too broadly could expose unsafe order/filter keys.

## Assumptions

- P043 added `entangled_rowid` to Postgres dynamic table DDL.
- Migration tooling will copy SQLite rowid into `entangled_rowid`.
