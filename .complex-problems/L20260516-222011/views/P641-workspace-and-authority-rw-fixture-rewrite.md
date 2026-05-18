# P641: Workspace and Authority RW Fixture Rewrite

Status: done
Parent: P639
Root: P000
Source Ticket: T634 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P641
Body: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P641/README.md
Ticket(s): T635

## Problem
Workspace and authority tests use `/rw/scratch` as generic writable paths. These should be neutral current paths while preserving write/read/tree/key-mapping invariants.

## Success Criteria
- Updates `test_workspace.py`, `test_workspace_limits.py`, and `test_workspace_authority.py` root scratch fixtures.
- Preserves missing path, binary IO, tree listing, append/read, and key mapping assertions.
- Runs focused tests for touched files.

## Subproblems
- none

## Results
- R629

## Latest Check
C670

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P641/README.md
- Ticket T635: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P641/tickets/T635.md
- Result R629: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P641/results/R629.md
- Check C670: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P641/checks/C670.md

## Follow-ups
- none
