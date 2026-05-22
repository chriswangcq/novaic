# P010: Classify Gateway and Cortex Postgres Boundaries

Status: done
Parent: P004
Root: P000
Source Ticket: T007 (split)
Source Check: none
Package: problems/P000/children/P004/children/P010
Body: problems/P000/children/P004/children/P010/README.md
Ticket(s): T019

## Problem
`gateway.db` contains auth/ops state while `cortex/operational.sqlite3` appears to be an operational projection/cache. They need explicit Postgres dispositions: migrate, defer, or retain as projection, with backup expectations and ownership notes.

This belongs under P004 because these stores are smaller than queue/Entangled but still have distinct ownership and runtime roles.

## Success Criteria
- `gateway.db` tables are classified as auth state, ops state, obsolete tables, or migration candidates.
- `cortex/operational.sqlite3` is classified as state owner or projection/cache with evidence.
- Backup expectations and eventual Postgres boundaries are documented.
- The central SQLite classification note is updated if disposition changes.
- No production cutover is attempted by this problem.

## Subproblems
- P021: Classify Gateway SQLite State and Postgres Boundary
- P022: Classify Cortex Operational SQLite State and Postgres Boundary
- P023: Synthesize Gateway Cortex SQLite Dispositions and Classification Note

## Results
- R020

## Latest Check
C020

## Bodies
- Problem: problems/P000/children/P004/children/P010/README.md
- Ticket T019: problems/P000/children/P004/children/P010/tickets/T019.md
- Result R020: problems/P000/children/P004/children/P010/results/R020.md
- Check C020: problems/P000/children/P004/children/P010/checks/C020.md

## Follow-ups
- none
