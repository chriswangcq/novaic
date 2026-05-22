# P102: Add Queue Migration Semantic Aggregate Validation

Status: done
Parent: P101
Root: P000
Source Ticket: T099 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P075/children/P101/children/P102
Body: problems/P000/children/P024/children/P028/children/P075/children/P101/children/P102/README.md
Ticket(s): T100

## Problem
The migration report needs to prove more than raw row counts. It must compare Queue-specific semantic aggregates between SQLite source and Postgres target so a copied database cannot silently lose task/saga/session states, outbox statuses, idempotency statuses, worker leases, event/outbox high-water marks, or schema version.

## Success Criteria
- Computes and compares row counts for every active migration table.
- Computes task, saga, and session state histograms.
- Computes outbox status counts for task, saga, worker lease, and session outbox tables.
- Computes idempotency status counts and worker lease state counts.
- Computes max ID/high-water values for event and outbox tables.
- Computes config schema version.
- Produces structured validation errors and a report status of `validated` or `error`.
- Tests cover validation success and at least one semantic mismatch failure.

## Subproblems
- none

## Results
- R096

## Latest Check
C104

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P075/children/P101/children/P102/README.md
- Ticket T100: problems/P000/children/P024/children/P028/children/P075/children/P101/children/P102/tickets/T100.md
- Result R096: problems/P000/children/P024/children/P028/children/P075/children/P101/children/P102/results/R096.md
- Check C104: problems/P000/children/P024/children/P028/children/P075/children/P101/children/P102/checks/C104.md

## Follow-ups
- none
