# Map Queue JSONB Timestamp Index and SQLite Assumption Blockers

## Problem

Queue SQL uses SQLite-specific JSON functions, text timestamps, partial indexes, WAL/busy timeout behavior, and process-local FIFO/sharded locks. Before implementation, these SQLite assumptions must be translated to explicit Postgres JSONB, time, index, transaction isolation, and error/defer policies.

This belongs under T010 because these cross-cutting SQL compatibility choices affect every queue subsystem and can quietly invalidate otherwise-correct FSM mappings.

## Success Criteria

- Every observed SQLite JSON use that affects correctness is mapped to Postgres JSONB operators/functions and an indexing strategy when needed.
- Timestamp storage is decided for PG migration, including comparison behavior for retry, heartbeat, stale cutoff, lease expiry, published/acked, and created/updated fields.
- Required Postgres indexes and unique constraints are mapped from the P012 inventory, including partial pending outbox and in-progress idempotency indexes.
- SQLite busy/locked handling in routes and the generic store is mapped to Postgres exception classes, retry/defer behavior, or removal.
- Process-local Python locks are classified as performance/fairness helpers, correctness boundaries, or residue; any correctness dependence must be replaced with database-level rules.
- Unsafe or ambiguous SQLite assumptions are listed as blockers for implementation.

