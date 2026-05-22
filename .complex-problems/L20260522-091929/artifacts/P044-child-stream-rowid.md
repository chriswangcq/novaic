# Port Entangled stream pagination and cleanup rowid semantics to Postgres

## Problem

Entangled stream/list cleanup paths use SQLite `rowid` as a stable tie-breaker for duplicate cursor values and default cleanup ordering. Port these paths to use Postgres `entangled_rowid`.

## Success Criteria

- Postgres `list_stream` cursor lookup selects `entangled_rowid AS _rid`.
- Postgres before/after pagination predicates compare `entangled_rowid` instead of `rowid`.
- Cleanup/default ordering uses `entangled_rowid DESC` where SQLite uses `rowid DESC`.
- Validation accepts the dialect-specific internal tie-break field safely.
- Tests cover duplicate cursor values and query generation for both SQLite and Postgres.
