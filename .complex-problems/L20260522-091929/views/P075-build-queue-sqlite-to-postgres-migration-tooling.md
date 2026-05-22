# P075: Build Queue SQLite To Postgres Migration Tooling

Status: done
Parent: P028
Root: P000
Source Ticket: T072 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P075
Body: problems/P000/children/P024/children/P028/children/P075/README.md
Ticket(s): T096

## Problem
Production `queue.db` is live and non-empty, with task/saga/session/lease/outbox/idempotency state. A safe cutover needs tooling that copies SQLite state into `novaic_queue`, converts JSON/time values correctly, preserves identities and row counts, and validates semantic invariants before any production restart.

## Success Criteria
- A migration command can read a SQLite queue source and write into a clean Postgres target.
- Migration preserves row counts for every active queue table.
- Migration preserves key semantic aggregates: task/saga/session states, pending outbox counts, idempotency statuses, worker lease states, max event/outbox IDs, and config schema version.
- JSON/time conversion is validated against representative fixture data.
- Migration report redacts DSNs/secrets and is suitable for production ledger artifacts.
- Tests cover planner/reporting, copy execution, and semantic validation.

## Subproblems
- P099: Build Queue Migration Planner And Redacted Report Model
- P100: Implement Queue SQLite To Postgres Copy Execution
- P101: Add Queue Migration Semantic Validation And CLI
- P104: Validate Queue Migration Timestamp Binding

## Results
- R099

## Latest Check
C109

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P075/README.md
- Ticket T096: problems/P000/children/P024/children/P028/children/P075/tickets/T096.md
- Result R099: problems/P000/children/P024/children/P028/children/P075/results/R099.md
- Check C107: problems/P000/children/P024/children/P028/children/P075/checks/C107.md
- Check C109: problems/P000/children/P024/children/P028/children/P075/checks/C109.md

## Follow-ups
- P104: Validate Queue Migration Timestamp Binding
