# P004: Remove Cortex and Entangled server SQLite fallback paths

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): T004

## Problem
Cortex operational state and Entangled entity engine still expose SQLite as default or selectable server persistence. Migration scripts and comments also teach old SQLite operational stores as current.

## Success Criteria
- Cortex runtime entry point defaults to Postgres operational store and does not accept SQLite as a production fallback.
- Entangled runtime entry point defaults to Postgres and no longer launches from SQLite db-path in current startup examples.
- Old Cortex/Entangled SQLite migration CLIs are retired from current executable paths when no longer needed.
- Remaining SQLite code, if any, is limited to non-production tests or explicitly recorded as a follow-up with reason.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P004/README.md
- Ticket T004: problems/P000/children/P004/tickets/T004.md
- Result R003: problems/P000/children/P004/results/R003.md
- Check C003: problems/P000/children/P004/checks/C003.md

## Follow-ups
- none
