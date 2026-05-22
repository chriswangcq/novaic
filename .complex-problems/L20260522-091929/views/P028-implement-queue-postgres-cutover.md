# P028: Implement Queue Postgres Cutover

Status: todo
Parent: P024
Root: P000
Source Ticket: T024 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028
Body: problems/P000/children/P024/children/P028/README.md
Ticket(s): T072

## Problem
Queue still owns the highest-risk active state in `/opt/novaic/data/queue.db`. It should be migrated to the existing `novaic_queue` Postgres database only after preserving task FSM, saga, lease, worker, session, outbox, idempotency, JSON/time, and locking semantics.

## Success Criteria
- Queue has a Postgres-backed production store for all active task, saga, lease, session, outbox, idempotency, and worker state.
- SQLite transaction/busy/locking behavior is preserved with Postgres transactions, row locks, `SKIP LOCKED`, unique constraints, or advisory locks as appropriate.
- Existing Queue SQLite state is backed up and migrated with row-count and semantic invariant checks.
- Queue service and workers are switched to Postgres and health/worker/API smoke checks pass.
- No active Queue writer continues to use `/opt/novaic/data/queue.db` after cutover.
- The old SQLite file is retained only as rollback evidence and documented in the central classification note.

## Subproblems
- P073: Implement Queue Postgres Schema And Database Boundary
- P074: Port Queue Repositories And FSM Semantics To Postgres
- P075: Build Queue SQLite To Postgres Migration Tooling
- P076: Validate Queue Postgres Mode In Staging
- P077: Execute Queue Production Postgres Cutover And Cleanup

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P024/children/P028/README.md
- Ticket T072: problems/P000/children/P024/children/P028/tickets/T072.md

## Follow-ups
- none
