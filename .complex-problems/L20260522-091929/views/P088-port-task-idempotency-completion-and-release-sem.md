# P088: Port Task Idempotency Completion And Release Semantics To Postgres

Status: done
Parent: P086
Root: P000
Source Ticket: T080 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P088
Body: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P088/README.md
Ticket(s): T082

## Problem
`complete_idempotency_execution` and `release_idempotency_execution` must preserve owner-token and task-id ownership checks in Postgres mode. Completion must not let a mismatched worker overwrite a result, and release must delete only the matching in-progress owner/task row. This belongs under T080 because completion and release close or unwind the same side-effect guard acquired by the idempotency ledger.

## Success Criteria
- Postgres completion updates only rows with matching `idempotency_key`, `status = 'in_progress'`, `owner_token`, and `task_id`.
- Completed results bind as JSONB-compatible native values in Postgres mode and JSON text in sqlite mode.
- Completion fallback/upsert behavior cannot overwrite an existing ledger row for a mismatched owner or task.
- Postgres release deletes only matching in-progress rows for the same owner token and task id.
- Empty idempotency-key behavior remains unchanged.
- Focused tests cover successful completion, owner mismatch, task mismatch, JSONB result binding, successful release, nonmatching release, and selected sqlite regressions.

## Subproblems
- none

## Results
- R077

## Latest Check
C082

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P088/README.md
- Ticket T082: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P088/tickets/T082.md
- Result R077: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P088/results/R077.md
- Check C082: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P088/checks/C082.md

## Follow-ups
- none
