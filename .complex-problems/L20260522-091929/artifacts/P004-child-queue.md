# Map Queue SQLite Semantics to Postgres

## Problem

`queue.db` is the highest-risk remaining SQLite state owner. Its task/saga/session/worker-lease FSM tables, outbox tables, idempotency ledger, recovery paths, SQLite busy handling, and locking assumptions must be mapped to Postgres primitives before any cutover or implementation migration.

This belongs under P004 because queue migration is semantically independent and too risky to bundle with other stores.

## Success Criteria

- Each queue table group is mapped to a Postgres table/index/JSONB strategy.
- SQLite transaction/busy behavior is mapped to Postgres transactions, `FOR UPDATE SKIP LOCKED`, unique constraints, and/or advisory locks.
- Outbox and idempotency semantics have explicit replay/claim guarantees.
- A no-cutover implementation plan and verification matrix exists.
- No production queue migration is attempted by this problem.
