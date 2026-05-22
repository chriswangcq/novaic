# P074: Port Queue Repositories And FSM Semantics To Postgres

Status: done
Parent: P028
Root: P000
Source Ticket: T072 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P074
Body: problems/P000/children/P024/children/P028/children/P074/README.md
Ticket(s): T075

## Problem
Queue repository code currently relies on SQLite SQL, process-local locks, `json_each`/`json_extract`, busy/locked exception strings, and SQLite transaction behavior. The task queue, saga repo, session repo, worker lease ledgers, generic FSM store, outbox workers, and idempotency ledger need Postgres-specific SQL and concurrency semantics.

## Success Criteria
- Task publish/claim/complete/fail/recover/release/cancel paths work under Postgres transactions.
- Saga create/claim/heartbeat/recover/launch/complete/fail/cancel paths work under Postgres transactions.
- Session dispatch/finalize/rebuild and outbox paths preserve no-input-loss and at-most-one-active-session semantics.
- Worker lease state/event writes and recovery use explicit Postgres row locks or compare-and-update patterns.
- Idempotency duplicate/in-progress/completed-result behavior is preserved.
- SQLite JSON and busy/locked assumptions are replaced by explicit Postgres JSONB and transient-error handling.
- Focused tests cover concurrency-sensitive and idempotency-sensitive paths.

## Subproblems
- P079: Build Queue Postgres Dialect And FSM Store Foundation
- P080: Port Task Queue And Idempotency Paths To Postgres
- P081: Port Saga Repository And Worker Lease Semantics To Postgres
- P082: Port Session And Outbox Semantics To Postgres
- P083: Replace SQLite Busy Handling With Postgres Transient Error Guards

## Results
- R093

## Latest Check
C101

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P074/README.md
- Ticket T075: problems/P000/children/P024/children/P028/children/P074/tickets/T075.md
- Result R093: problems/P000/children/P024/children/P028/children/P074/results/R093.md
- Check C101: problems/P000/children/P024/children/P028/children/P074/checks/C101.md

## Follow-ups
- none
