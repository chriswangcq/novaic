# P635: RW Scratch Usage Inventory

Status: done
Parent: P631
Root: P000
Source Ticket: T630 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P631/children/P635
Body: problems/P000/children/P005/children/P554/children/P631/children/P635/README.md
Ticket(s): T631

## Problem
Root `/rw/scratch` appears in Workspace initialization and many tests. Before editing, classify which hits encode the old global scratch layout and which are generic arbitrary `/rw` path fixtures.

## Success Criteria
- Records exact scans for `/rw/scratch`, `RW_SCRATCH`, `/rw/subagents`, and `initialize_layout` across Cortex and LogicalFS.
- Classifies every relevant hit into current subagent-aware contract, generic RW fixture, removable legacy layout, or out-of-scope lower-layer test.
- Produces an exact edit target list for cleanup.

## Subproblems
- none

## Results
- R627

## Latest Check
C668

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P631/children/P635/README.md
- Ticket T631: problems/P000/children/P005/children/P554/children/P631/children/P635/tickets/T631.md
- Result R627: problems/P000/children/P005/children/P554/children/P631/children/P635/results/R627.md
- Check C668: problems/P000/children/P005/children/P554/children/P631/children/P635/checks/C668.md

## Follow-ups
- none
