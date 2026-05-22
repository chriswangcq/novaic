# P017: Map Queue JSONB Timestamp Index and SQLite Assumption Blockers

Status: done
Parent: P013
Root: P000
Source Ticket: T010 (split)
Source Check: none
Package: problems/P000/children/P004/children/P008/children/P013/children/P017
Body: problems/P000/children/P004/children/P008/children/P013/children/P017/README.md
Ticket(s): T013

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

## Subproblems
- none

## Results
- R009

## Latest Check
C009

## Bodies
- Problem: problems/P000/children/P004/children/P008/children/P013/children/P017/README.md
- Ticket T013: problems/P000/children/P004/children/P008/children/P013/children/P017/tickets/T013.md
- Result R009: problems/P000/children/P004/children/P008/children/P013/children/P017/results/R009.md
- Check C009: problems/P000/children/P004/children/P008/children/P013/children/P017/checks/C009.md

## Follow-ups
- none
