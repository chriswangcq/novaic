# P010: Git and submodule state fact capture

Status: done
Parent: P008
Root: P000
Source Ticket: T002 (split)
Source Check: none
Package: problems/P000/children/P001/children/P008/children/P010
Body: problems/P000/children/P001/children/P008/children/P010/README.md
Ticket(s): T003

## Problem
Capture the current git branch, dirty state, and submodule pointer state for the superproject and key submodules. This is read-only evidence needed before optimization.

## Success Criteria
- Superproject branch and dirty state are recorded.
- Submodule status is summarized.
- Key submodule dirty states are sampled or checked.
- Result explicitly states whether implementation files were modified during this fact capture.

## Subproblems
- P012: Superproject git state capture
- P013: Submodule git state capture

## Results
- R003

## Latest Check
C004

## Bodies
- Problem: problems/P000/children/P001/children/P008/children/P010/README.md
- Ticket T003: problems/P000/children/P001/children/P008/children/P010/tickets/T003.md
- Result R003: problems/P000/children/P001/children/P008/children/P010/results/R003.md
- Check C004: problems/P000/children/P001/children/P008/children/P010/checks/C004.md

## Follow-ups
- none
