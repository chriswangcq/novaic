# P106: Run Queue Service Postgres API Staging Smokes

Status: followup
Parent: P076
Root: P000
Source Ticket: T103 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P076/children/P106
Body: problems/P000/children/P024/children/P028/children/P076/children/P106/README.md
Ticket(s): T105

## Problem
After the staging Postgres target exists, Queue Service must start in Postgres mode and representative Queue APIs must work against the real service runtime, not only unit tests.

## Success Criteria
- Queue Service starts with `NOVAIC_QUEUE_DB_BACKEND=postgres` against the staging target.
- Health/readiness endpoints pass.
- Task publish/claim/complete/fail or safe retry equivalent passes.
- Saga create/claim/launch/complete/fail or safe equivalent passes.
- Session dispatch/finalize/rebuild or safe equivalent smoke passes.
- Idempotency duplicate/in-progress/completed-result smoke passes.
- DB counts after smokes are recorded with secrets redacted.

## Subproblems
- P109: Confirm Queue API Staging Target And Run Smokes

## Results
- R102

## Latest Check
C111

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P106/README.md
- Ticket T105: problems/P000/children/P024/children/P028/children/P076/children/P106/tickets/T105.md
- Result R102: problems/P000/children/P024/children/P028/children/P076/children/P106/results/R102.md
- Check C111: problems/P000/children/P024/children/P028/children/P076/children/P106/checks/C111.md

## Follow-ups
- P109: Confirm Queue API Staging Target And Run Smokes
