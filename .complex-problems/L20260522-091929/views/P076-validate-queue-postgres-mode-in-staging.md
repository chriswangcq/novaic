# P076: Validate Queue Postgres Mode In Staging

Status: done
Parent: P028
Root: P000
Source Ticket: T072 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P076
Body: problems/P000/children/P024/children/P028/children/P076/README.md
Ticket(s): T103

## Problem
Before production cutover, Queue Postgres mode must be exercised with the queue service, workers, outbox workers, and representative APIs against a non-production Postgres target. Unit tests alone cannot prove worker claim/recover/outbox/idempotency behavior under an actual service runtime.

## Success Criteria
- A staging/test Queue Postgres database is prepared without touching production queue data.
- Queue service starts in Postgres mode and reports healthy/ready.
- Representative task publish/claim/complete/retry or safe equivalents pass.
- Representative saga/session/outbox/idempotency smokes pass.
- Worker/outbox processes can run against Postgres mode without SQLite file holders.
- Staging report records commands, checks, counts, and secret redaction.

## Subproblems
- P105: Prepare Queue Postgres Staging Target
- P106: Run Queue Service Postgres API Staging Smokes
- P107: Run Queue Worker And Outbox Postgres Staging Smokes
- P108: Record Queue Postgres Staging Validation Report

## Results
- R117

## Latest Check
C132

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/README.md
- Ticket T103: problems/P000/children/P024/children/P028/children/P076/tickets/T103.md
- Result R117: problems/P000/children/P024/children/P028/children/P076/results/R117.md
- Check C132: problems/P000/children/P024/children/P028/children/P076/checks/C132.md

## Follow-ups
- none
