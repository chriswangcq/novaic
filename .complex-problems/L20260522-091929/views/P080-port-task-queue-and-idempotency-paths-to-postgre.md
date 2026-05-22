# P080: Port Task Queue And Idempotency Paths To Postgres

Status: done
Parent: P074
Root: P000
Source Ticket: T075 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P074/children/P080
Body: problems/P000/children/P024/children/P028/children/P074/children/P080/README.md
Ticket(s): T077

## Problem
`queue_service/queue_db.py` still uses SQLite `datetime(...)`, `json_each`, `json_extract`, local busy-timeout hints, and SQLite-flavored idempotency SQL. Task publish/claim/complete/fail/recover/release/cancel and idempotency duplicate handling must work under Postgres row locks, JSONB predicates, native timestamptz comparisons, and explicit transaction semantics. This belongs under P074 because task correctness and idempotency are one tightly coupled repository slice.

## Success Criteria
- Task claim uses Postgres-safe candidate selection and locking, including `FOR UPDATE SKIP LOCKED` or an equivalent explicit compare-and-update pattern.
- Task single-row mutations use explicit task-state locking or compare-and-update semantics instead of process-local SQLite locks.
- Task retry/stale recovery uses native timestamptz comparisons rather than SQLite `datetime(...)`.
- Task dependency readiness and cancel-by-agent use JSONB predicates rather than `json_each`/`json_extract`.
- Idempotency in-progress/completed/duplicate-result behavior is preserved under Postgres transactions.
- Focused tests cover duplicate claim losers, completion/recovery races, JSONB dependency readiness, cancel-by-agent, and idempotency completed/in-progress cases without production access.

## Subproblems
- P084: Add Task Queue Postgres Claim Recovery And JSONB Query Dialect
- P085: Port Task Mutations And State Locking To Postgres
- P086: Port Task Idempotency Ledger To Postgres

## Results
- R080

## Latest Check
C085

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P074/children/P080/README.md
- Ticket T077: problems/P000/children/P024/children/P028/children/P074/children/P080/tickets/T077.md
- Result R080: problems/P000/children/P024/children/P028/children/P074/children/P080/results/R080.md
- Check C085: problems/P000/children/P024/children/P028/children/P074/children/P080/checks/C085.md

## Follow-ups
- none
