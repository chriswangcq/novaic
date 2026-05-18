# P213: Delete stale `resolve_for_llm` tests

Status: done
Parent: P200
Root: P000
Source Ticket: T202 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P200/children/P213
Body: problems/P000/children/P003/children/P127/children/P187/children/P200/children/P213/README.md
Ticket(s): T203

## Problem
`novaic-cortex/tests/test_resolve_for_llm.py` tests the removed `resolve_for_llm` helper and asserts the obsolete inline-image/base64 behavior. It should be physically deleted.

## Success Criteria
- The stale test file is deleted.
- `rg "resolve_for_llm"` finds no production or test references except ledger/docs notes.
- Focused Cortex tests pass without that file.

## Subproblems
- none

## Results
- R198

## Latest Check
C212

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P200/children/P213/README.md
- Ticket T203: problems/P000/children/P003/children/P127/children/P187/children/P200/children/P213/tickets/T203.md
- Result R198: problems/P000/children/P003/children/P127/children/P187/children/P200/children/P213/results/R198.md
- Check C212: problems/P000/children/P003/children/P127/children/P187/children/P200/children/P213/checks/C212.md

## Follow-ups
- none
