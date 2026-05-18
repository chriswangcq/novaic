# P346: Session-ended delivery tests compatibility cleanup

Status: done
Parent: P343
Root: P000
Source Ticket: T331 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P346
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P346/README.md
Ticket(s): T333

## Problem
Tests must not bless zero-generation session-ended/finalize delivery as valid. Existing tests should either assert failure for zero/missing generation or be clearly outside the session-ended delivery boundary.

## Success Criteria
- Search tests for `session_generation=0`, `"session_generation": 0`, `generation=0`, and zero-generation assertions near finalize/session-ended.
- Rewrite any P336 delivery-boundary test that treats zero generation as valid.
- Explicitly classify unrelated or upstream tests as delegated to other tickets.

## Subproblems
- none

## Results
- R326

## Latest Check
C347

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P346/README.md
- Ticket T333: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P346/tickets/T333.md
- Result R326: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P346/results/R326.md
- Check C347: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P336/children/P343/children/P346/checks/C347.md

## Follow-ups
- none
