# P112: Run Queue Service API Smokes

Status: done
Parent: P109
Root: P000
Source Ticket: T106 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P112
Body: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P112/README.md
Ticket(s): T116

## Problem
With Queue Service running in Postgres mode, representative Queue APIs must be exercised against the real service runtime. This child belongs under T106 because API behavior failures should be diagnosed separately from startup and database target setup.

## Success Criteria
- Health/readiness smoke passes.
- Task publish/claim/complete/fail or safe retry equivalent passes.
- Saga create/claim/launch/complete/fail or safe equivalent passes.
- Session dispatch/finalize/rebuild or safe equivalent passes.
- Idempotency duplicate/in-progress/completed-result smoke passes.
- Each skipped operation has an explicit safety or environment reason.

## Subproblems
- none

## Results
- R112

## Latest Check
C126

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P112/README.md
- Ticket T116: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P112/tickets/T116.md
- Result R112: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P112/results/R112.md
- Check C126: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P112/checks/C126.md

## Follow-ups
- none
