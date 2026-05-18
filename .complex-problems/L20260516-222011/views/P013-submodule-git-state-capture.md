# P013: Submodule git state capture

Status: done
Parent: P010
Root: P000
Source Ticket: T003 (split)
Source Check: none
Package: problems/P000/children/P001/children/P008/children/P010/children/P013
Body: problems/P000/children/P001/children/P008/children/P010/children/P013/README.md
Ticket(s): T005

## Problem
Capture submodule pointers and dirty states for active submodules so later changes are attributed to the correct repository.

## Success Criteria
- `git submodule status` is summarized.
- Key changed or active submodules have `git status --short` checked.
- Dirty submodule markers are explained if present.
- No code edits are made.

## Subproblems
- P014: Repair submodule dirty-state capture

## Results
- R001

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P001/children/P008/children/P010/children/P013/README.md
- Ticket T005: problems/P000/children/P001/children/P008/children/P010/children/P013/tickets/T005.md
- Result R001: problems/P000/children/P001/children/P008/children/P010/children/P013/results/R001.md
- Check C001: problems/P000/children/P001/children/P008/children/P010/children/P013/checks/C001.md
- Check C003: problems/P000/children/P001/children/P008/children/P010/children/P013/checks/C003.md

## Follow-ups
- P014: Repair submodule dirty-state capture
