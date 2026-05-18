# P422: ContextEvent projection and read-model cleanup

Status: done
Parent: P417
Root: P000
Source Ticket: T407 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P422
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P422/README.md
Ticket(s): T409

## Problem
ContextEvent projection/read-model code may contain legitimate projection state, but it must not silently revive old compatibility channels or inline payload behavior.

## Success Criteria
- Inspect `context_event_projection.py`, `context_event_read_model.py`, and related projection tests.
- Classify generation/archive/context hits as read-model state, diagnostics, or dangerous compatibility residue.
- Patch dangerous compatibility behavior if found.
- Add or update focused projection/read-model tests for changed behavior.
- Run projection/read-model tests.

## Subproblems
- none

## Results
- R402

## Latest Check
C428

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P422/README.md
- Ticket T409: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P422/tickets/T409.md
- Result R402: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P422/results/R402.md
- Check C428: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P422/checks/C428.md

## Follow-ups
- none
