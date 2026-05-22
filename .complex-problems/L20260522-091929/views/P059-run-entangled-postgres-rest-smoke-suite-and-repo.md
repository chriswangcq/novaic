# P059: Run Entangled Postgres REST Smoke Suite And Report

Status: done
Parent: P051
Root: P000
Source Ticket: T052 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P059
Body: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P059/README.md
Ticket(s): T055

## Problem
With the Postgres-mode runtime running, run representative REST smokes and capture a redacted report. This belongs under `P051` because production cutover needs concrete API proof, not only process readiness.

## Success Criteria
- REST smokes cover health/readiness plus representative list/read, singleton upsert/read, stream append/query, update, delete, and CAS or equivalent rowcount-sensitive behavior.
- Schema registration succeeds or existing registered schemas are proven available.
- Smoke output includes endpoint statuses, entity/table names, counts, and mutation cleanup evidence.
- Auth/service-token requirements are satisfied safely or a narrow blocker/follow-up is created.
- Report is written under ledger artifacts and contains no DSNs, service tokens, cookies, or env-file contents.
- Staging process is stopped or confirmed safe to leave only if explicitly intended.

## Subproblems
- none

## Results
- R051

## Latest Check
C053

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P059/README.md
- Ticket T055: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P059/tickets/T055.md
- Result R051: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P059/results/R051.md
- Check C053: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P059/checks/C053.md

## Follow-ups
- none
