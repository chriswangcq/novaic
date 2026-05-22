# P057: Prepare Safe Entangled Postgres REST Staging Target

Status: done
Parent: P051
Root: P000
Source Ticket: T052 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P057
Body: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P057/README.md
Ticket(s): T053

## Problem
Before REST smokes can run, there must be a safe Postgres target with migrated or fixture data that is not production traffic-facing. Prepare that target, import data using the migration command or an equivalent staging-safe path, and record a redacted setup report. This belongs under `P051` because runtime REST validation needs a concrete Postgres target.

## Success Criteria
- A safe Postgres database/target is selected or created for REST staging without touching production traffic.
- DSN handling uses a redacted secret file or non-secret test connection label.
- Migration/import runs against the staging target or a clear fixture target with no production mutations.
- Setup report records target label, migrated tables/counts, semantic checks, and cleanup state without secrets.
- Any target setup blocker is documented with exact commands/results and no raw secrets.

## Subproblems
- none

## Results
- R049

## Latest Check
C051

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P057/README.md
- Ticket T053: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P057/tickets/T053.md
- Result R049: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P057/results/R049.md
- Check C051: problems/P000/children/P024/children/P027/children/P040/children/P051/children/P057/checks/C051.md

## Follow-ups
- none
