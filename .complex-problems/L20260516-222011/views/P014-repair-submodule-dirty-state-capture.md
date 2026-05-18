# P014: Repair submodule dirty-state capture

Status: done
Parent: P013
Root: P000
Source Ticket: none (none)
Source Check: C001
Package: problems/P000/children/P001/children/P008/children/P010/children/P013/children/P014
Body: problems/P000/children/P001/children/P008/children/P010/children/P013/children/P014/README.md
Ticket(s): T006

## Problem
Redo the per-submodule dirty-state capture with a robust command that does not trigger shell `printf` option parsing errors. Record corrected evidence for submodule branch/status boundaries.

## Success Criteria
- Per-submodule output includes clear headers or path labels.
- Each submodule branch and `git status --short` output is captured or explicitly bounded.
- The command exits without the previous `printf: --: invalid option` errors.
- The result supersedes the weak dirty-state claim in R001.

## Subproblems
- none

## Results
- R002

## Latest Check
C002

## Bodies
- Problem: problems/P000/children/P001/children/P008/children/P010/children/P013/children/P014/README.md
- Ticket T006: problems/P000/children/P001/children/P008/children/P010/children/P013/children/P014/tickets/T006.md
- Result R002: problems/P000/children/P001/children/P008/children/P010/children/P013/children/P014/results/R002.md
- Check C002: problems/P000/children/P001/children/P008/children/P010/children/P013/children/P014/checks/C002.md

## Follow-ups
- none
