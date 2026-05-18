# P478: Rerun hidden input focused tests from correct runtime cwd

Status: done
Parent: P474
Root: P000
Source Ticket: none (none)
Source Check: C489
Package: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P474/children/P478
Body: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P474/children/P478/README.md
Ticket(s): T469

## Problem
The P474 focused pytest command failed because relative-path guard tests were run from the repo root instead of `novaic-agent-runtime`. Rerun the same focused suite from the correct cwd and preserve guard artifacts.

## Success Criteria
- Run the focused pytest suite from `novaic-agent-runtime` or otherwise make relative-path tests resolve correctly.
- Save rerun logs under `.complex-problems/L20260516-222011/tmp/p478/`.
- Confirm hidden-input guards still pass.
- Record whether the verification now passes or exposes a real code/test issue.

## Subproblems
- none

## Results
- R463

## Latest Check
C490

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P474/children/P478/README.md
- Ticket T469: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P474/children/P478/tickets/T469.md
- Result R463: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P474/children/P478/results/R463.md
- Check C490: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/children/P474/children/P478/checks/C490.md

## Follow-ups
- none
