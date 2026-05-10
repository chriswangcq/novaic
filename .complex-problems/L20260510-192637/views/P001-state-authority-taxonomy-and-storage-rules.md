# P001: State Authority Taxonomy And Storage Rules

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Cortex needs a clear rule for what state may live in LogicalFS/Workspace, SQLite, Redis, Blob, or process memory. Without this taxonomy, future work can accidentally move semantic authority into caches, locks, or artifact stores.

## Success Criteria
- Define state classes: semantic authority, event ledger, projection, coordination lease, artifact bytes, observability, process cache/config.
- Decide allowed storage engines for each class: LogicalFS/Workspace, SQLite, Redis, Blob, memory.
- Define invariants for recovery, replay, migration, and tests.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
