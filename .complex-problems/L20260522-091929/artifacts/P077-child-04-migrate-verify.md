# Migrate Queue SQLite Data To Production Postgres And Verify

## Problem

The production SQLite queue contents must be copied into `novaic_queue` with schema version, row counts, JSON payloads, FSM projections, outbox state, lease state, and idempotency semantics verified before services restart on Postgres.

## Success Criteria

- Migration tooling runs against the frozen SQLite backup/source and production Postgres target.
- Row counts match expected source-to-target mappings for all Queue tables.
- Semantic invariant checks cover task state, saga state, session/outbox rows, worker lease rows, and idempotency completed/in-progress rows.
- Any migration warnings or skipped rows are recorded and resolved or block cutover.
- A redacted migration report is saved under ledger artifacts.
