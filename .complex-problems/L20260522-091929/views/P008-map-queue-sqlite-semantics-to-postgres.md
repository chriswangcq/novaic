# P008: Map Queue SQLite Semantics to Postgres

Status: done
Parent: P004
Root: P000
Source Ticket: T007 (split)
Source Check: none
Package: problems/P000/children/P004/children/P008
Body: problems/P000/children/P004/children/P008/README.md
Ticket(s): T008

## Problem
`queue.db` is the highest-risk remaining SQLite state owner. Its task/saga/session/worker-lease FSM tables, outbox tables, idempotency ledger, recovery paths, SQLite busy handling, and locking assumptions must be mapped to Postgres primitives before any cutover or implementation migration.

This belongs under P004 because queue migration is semantically independent and too risky to bundle with other stores.

## Success Criteria
- Each queue table group is mapped to a Postgres table/index/JSONB strategy.
- SQLite transaction/busy behavior is mapped to Postgres transactions, `FOR UPDATE SKIP LOCKED`, unique constraints, and/or advisory locks.
- Outbox and idempotency semantics have explicit replay/claim guarantees.
- A no-cutover implementation plan and verification matrix exists.
- No production queue migration is attempted by this problem.

## Subproblems
- P012: Inventory Queue SQLite Schema and Runtime Owners
- P013: Map Queue FSM, Claim, Outbox, Lease, and Idempotency Semantics
- P014: Define Queue Postgres Implementation and Cutover Plan

## Results
- R012

## Latest Check
C012

## Bodies
- Problem: problems/P000/children/P004/children/P008/README.md
- Ticket T008: problems/P000/children/P004/children/P008/tickets/T008.md
- Result R012: problems/P000/children/P004/children/P008/results/R012.md
- Check C012: problems/P000/children/P004/children/P008/checks/C012.md

## Follow-ups
- none
