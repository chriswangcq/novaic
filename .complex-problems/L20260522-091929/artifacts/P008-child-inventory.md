# Inventory Queue SQLite Schema and Runtime Owners

## Problem

Before mapping queue semantics to Postgres, the current production `queue.db` schema, row counts, indexes, and runtime owners must be captured from evidence. This prevents the migration plan from being based on stale source assumptions.

## Success Criteria

- Production table list, schemas, indexes, triggers, and row counts are captured.
- Queue runtime processes that hold or use `queue.db` are identified.
- Queue code modules that own each table group are mapped.
- A durable inventory artifact exists locally and on the `api` host.
- No production queue data is mutated.
