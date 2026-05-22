# P110: Confirm Non-Production Queue Postgres Target

Status: done
Parent: P109
Root: P000
Source Ticket: T106 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P110
Body: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P110/README.md
Ticket(s): T107

## Problem
P109 needs a confirmed non-production Queue Postgres DSN or DSN file before any Queue Service startup or API smoke can safely run. This child belongs under T106 because target confirmation is the hard safety gate and current evidence shows the local shell lacks `NOVAIC_QUEUE_POSTGRES_DSN_FILE` and `NOVAIC_QUEUE_POSTGRES_DSN`.

## Success Criteria
- A Queue Postgres DSN file or direct DSN is available to the smoke runner.
- The target is confirmed non-production by hostname/database naming, deployment context, or explicit user-provided confirmation.
- The target public identity is recorded with DSNs/secrets redacted.
- If no target can be confirmed, an explicit blocker is recorded with exact environment variables or file path required.

## Subproblems
- none

## Results
- R103

## Latest Check
C112

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P110/README.md
- Ticket T107: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P110/tickets/T107.md
- Result R103: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P110/results/R103.md
- Check C112: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P110/checks/C112.md

## Follow-ups
- none
