# Build Queue SQLite To Postgres Migration Tooling

## Problem

Production `queue.db` is live and non-empty, with task/saga/session/lease/outbox/idempotency state. A safe cutover needs tooling that copies SQLite state into `novaic_queue`, converts JSON/time values correctly, preserves identities and row counts, and validates semantic invariants before any production restart.

## Success Criteria

- A migration command can read a SQLite queue source and write into a clean Postgres target.
- Migration preserves row counts for every active queue table.
- Migration preserves key semantic aggregates: task/saga/session states, pending outbox counts, idempotency statuses, worker lease states, max event/outbox IDs, and config schema version.
- JSON/time conversion is validated against representative fixture data.
- Migration report redacts DSNs/secrets and is suitable for production ledger artifacts.
- Tests cover planner/reporting, copy execution, and semantic validation.
