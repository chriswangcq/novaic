# P082: Port Session And Outbox Semantics To Postgres

Status: done
Parent: P074
Root: P000
Source Ticket: T075 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P074/children/P082
Body: problems/P000/children/P024/children/P028/children/P074/children/P082/README.md
Ticket(s): T088

## Problem
Session dispatch/finalize/rebuild and task/saga/session/lease outbox paths must preserve no-input-loss, at-most-one-active-session, and publish-before-ack retry semantics under Postgres. Current code was built around SQLite store behavior and process-local locking; the Postgres path needs explicit row locking, deterministic ordering, and outbox claim semantics. This belongs under P074 because session coordination and outbox delivery are correctness-critical but separable from task/saga repository ports.

## Success Criteria
- Session first-dispatch/attach/finalize ensures and locks `tq_session_state(session_key)` or uses an equivalent explicit compare-and-update pattern.
- Session rebuild and read models operate on Postgres-safe SQL and deterministic ordering.
- Outbox drain paths claim rows before external publish or document/enforce a single-worker constraint for the first Postgres runtime.
- Pending/dead-letter outbox status transitions preserve retry semantics under Postgres transactions.
- No-input-loss and at-most-one-active-session semantics are covered by focused tests in the Postgres path.
- Tests cover session first-dispatch races, attach/finalize behavior, outbox publish-before-ack retry, and deterministic outbox ordering.

## Subproblems
- P093: Port Session State Locking And Transition Semantics To Postgres
- P094: Port Durable Outbox Drain And Retry Semantics To Postgres
- P095: Isolate Session And Outbox SQLite Runtime Residue
- P097: Port Session Rebuild And Read Models To Postgres

## Results
- R089

## Latest Check
C097

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P074/children/P082/README.md
- Ticket T088: problems/P000/children/P024/children/P028/children/P074/children/P082/tickets/T088.md
- Result R089: problems/P000/children/P024/children/P028/children/P074/children/P082/results/R089.md
- Check C095: problems/P000/children/P024/children/P028/children/P074/children/P082/checks/C095.md
- Check C097: problems/P000/children/P024/children/P028/children/P074/children/P082/checks/C097.md

## Follow-ups
- P097: Port Session Rebuild And Read Models To Postgres
