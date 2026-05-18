# P173: Context read handler residue classification

Status: done
Parent: P162
Root: P000
Source Ticket: T159 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P173
Body: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P173/README.md
Ticket(s): T160

## Problem
`context_handlers.py` still serves explicit context-read topics. These paths must be classified as safe user/tool inspection paths or stale provider-input fallbacks.

## Success Criteria
- `context_handlers.py` is mapped with line pointers.
- Topic/caller intent for context read is classified.
- Tests covering context-read behavior are identified and run.
- Any stale provider-input use is fixed or split.

## Subproblems
- none

## Results
- R155

## Latest Check
C169

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P173/README.md
- Ticket T160: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P173/tickets/T160.md
- Result R155: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P173/results/R155.md
- Check C169: problems/P000/children/P003/children/P126/children/P135/children/P162/children/P173/checks/C169.md

## Follow-ups
- none
