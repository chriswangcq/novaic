# P002: Remove Queue Service SQLite runtime fallback

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
Queue Service still exposes SQLite backend choices, queue.db path construction, migration CLIs, and tests that preserve SQLite compatibility as current behavior. This directly conflicts with the Postgres-only server persistence target.

## Success Criteria
- Queue Service runtime entry points use Postgres as the only server backend and no longer offer a SQLite backend selector.
- Queue worker database assembly no longer constructs or logs queue.db paths.
- Old Queue SQLite-to-Postgres migration CLIs/modules/tests are removed from current executable paths.
- Focused Queue tests and residue scans pass for the Postgres-only boundary.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R001: problems/P000/children/P002/results/R001.md
- Check C001: problems/P000/children/P002/checks/C001.md

## Follow-ups
- none
