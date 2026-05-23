# P003: Remove Gateway and Device server SQLite utilities

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P003
Body: problems/P000/children/P003/README.md
Ticket(s): T003

## Problem
Gateway and Device still contain SQLite backend defaults, gateway.db admin/migration scripts, and device local DB modules/comments. These paths make deleted gateway.db/device.db files look recoverable and supported.

## Success Criteria
- Gateway startup defaults to Postgres-only auth/config storage and rejects SQLite backend selection in current server runtime.
- Gateway SQLite migration/admin scripts are deleted from current executable paths or replaced with Postgres-only equivalents if still needed.
- Device local SQLite modules and comments that claim active SQLite ownership are deleted or rewritten to the Entangled/EntityStore current path.
- Focused Gateway/Device tests or imports pass after deletion.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P003/README.md
- Ticket T003: problems/P000/children/P003/tickets/T003.md
- Result R002: problems/P000/children/P003/results/R002.md
- Check C002: problems/P000/children/P003/checks/C002.md

## Follow-ups
- none
