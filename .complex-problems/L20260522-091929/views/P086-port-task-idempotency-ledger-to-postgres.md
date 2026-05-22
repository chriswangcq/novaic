# P086: Port Task Idempotency Ledger To Postgres

Status: done
Parent: P080
Root: P000
Source Ticket: T077 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086
Body: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/README.md
Ticket(s): T080

## Problem
Task idempotency acquisition, completion, release, and diagnostics currently use SQLite-shaped SQL and Python timestamp parsing around `tq_idempotency_ledger`. The Postgres path must preserve in-progress leases, owner-token checks, completed-result reuse, contention counts, and duplicate behavior with native timestamptz and transaction-safe upserts. This belongs under P080 because idempotency guards external side effects and should be verified separately from task claim/mutation SQL.

## Success Criteria
- Postgres idempotency acquisition locks or atomically updates the `idempotency_key` row and preserves completed-result reuse.
- In-progress lease checks use native timestamptz comparisons instead of Python-side ISO parsing for the Postgres path.
- Completion updates require matching owner token and task id, preserving completed results as JSONB-compatible values.
- Release deletes only matching in-progress owner/task rows.
- Diagnostics return the same public shape without relying on tuple-only row access.
- Focused tests cover missing key, new acquisition, active in-progress duplicate, expired lease reacquire, completed duplicate, completion owner mismatch, release, and diagnostics ordering.

## Subproblems
- P087: Port Task Idempotency Acquisition And Lease Semantics To Postgres
- P088: Port Task Idempotency Completion And Release Semantics To Postgres
- P089: Normalize Task Idempotency Diagnostics Across SQLite And Postgres

## Results
- R079

## Latest Check
C084

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/README.md
- Ticket T080: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/tickets/T080.md
- Result R079: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/results/R079.md
- Check C084: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/checks/C084.md

## Follow-ups
- none
