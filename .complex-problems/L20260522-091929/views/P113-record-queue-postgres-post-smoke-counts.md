# P113: Record Queue Postgres Post-Smoke Counts

Status: done
Parent: P109
Root: P000
Source Ticket: T106 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P113
Body: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P113/README.md
Ticket(s): T117

## Problem
After API smokes run, Queue Postgres table counts and target public info must be recorded so P109/P106 have durable evidence of what changed. This child belongs under T106 because count/reporting evidence is separate from endpoint success.

## Success Criteria
- Post-smoke counts are recorded for Queue migration tables.
- Target public info is recorded with DSNs/secrets redacted.
- Counts are tied to the smoke run artifact or command evidence.
- Any count query failure is recorded with enough detail to diagnose without exposing secrets.

## Subproblems
- none

## Results
- R113

## Latest Check
C127

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P113/README.md
- Ticket T117: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P113/tickets/T117.md
- Result R113: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P113/results/R113.md
- Check C127: problems/P000/children/P024/children/P028/children/P076/children/P106/children/P109/children/P113/checks/C127.md

## Follow-ups
- none
