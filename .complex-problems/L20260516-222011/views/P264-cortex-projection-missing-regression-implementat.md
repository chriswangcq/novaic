# P264: Cortex projection missing regression implementation

Status: done
Parent: P259
Root: P000
Source Ticket: T255 (split)
Source Check: none
Package: problems/P000/children/P003/children/P132/children/P259/children/P264
Body: problems/P000/children/P003/children/P132/children/P259/children/P264/README.md
Ticket(s): T257

## Problem
If the inventory finds missing Cortex projection coverage, add the smallest focused test changes to close the gaps.

## Success Criteria
- Missing regression tests are added or adjusted if needed.
- Tests assert no raw media/base64 is present in history/current non-display projection.
- Tests preserve explicit display perception as the only allowed media projection mode.
- No unrelated refactor or compatibility branch is introduced.

## Subproblems
- none

## Results
- R253

## Latest Check
C268

## Bodies
- Problem: problems/P000/children/P003/children/P132/children/P259/children/P264/README.md
- Ticket T257: problems/P000/children/P003/children/P132/children/P259/children/P264/tickets/T257.md
- Result R253: problems/P000/children/P003/children/P132/children/P259/children/P264/results/R253.md
- Check C268: problems/P000/children/P003/children/P132/children/P259/children/P264/checks/C268.md

## Follow-ups
- none
