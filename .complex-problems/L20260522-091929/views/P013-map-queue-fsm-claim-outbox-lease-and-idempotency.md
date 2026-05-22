# P013: Map Queue FSM, Claim, Outbox, Lease, and Idempotency Semantics

Status: done
Parent: P008
Root: P000
Source Ticket: T008 (split)
Source Check: none
Package: problems/P000/children/P004/children/P008/children/P013
Body: problems/P000/children/P004/children/P008/children/P013/README.md
Ticket(s): T010

## Problem
Queue correctness depends on FSM transition ledgers, state projections, task/saga/session outboxes, worker leases, idempotency, recovery, and SQLite busy/transaction behavior. These must be mapped to Postgres behavior before implementation.

## Success Criteria
- Task, saga, session, and worker-lease FSM writes are mapped to Postgres transaction patterns.
- Claim/recovery behavior is mapped to `FOR UPDATE SKIP LOCKED`, uniqueness, retry, and/or advisory-lock rules.
- Outbox and idempotency replay guarantees are stated.
- JSON field use is mapped to JSONB/operator/index strategy.
- Unsafe or ambiguous SQLite assumptions are listed as blockers for implementation.

## Subproblems
- P015: Map Task Saga and Worker Lease Postgres Concurrency Semantics
- P016: Map Session Outbox and Idempotency Postgres Replay Semantics
- P017: Map Queue JSONB Timestamp Index and SQLite Assumption Blockers

## Results
- R010

## Latest Check
C010

## Bodies
- Problem: problems/P000/children/P004/children/P008/children/P013/README.md
- Ticket T010: problems/P000/children/P004/children/P008/children/P013/tickets/T010.md
- Result R010: problems/P000/children/P004/children/P008/children/P013/results/R010.md
- Check C010: problems/P000/children/P004/children/P008/children/P013/checks/C010.md

## Follow-ups
- none
