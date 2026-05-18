# P316: Update session outbox boundary source guards

Status: done
Parent: P314
Root: P000
Source Ticket: T302 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P316
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P316/README.md
Ticket(s): T304

## Problem
`test_pr281_session_outbox_wrapper_boundary.py` still asserts the older single wake outbox source shape. The current implementation uses a generic wrapper shape for outbox effect lists, so the test should guard the intended boundary without preserving stale source assumptions.

## Success Criteria
- The boundary test still rejects repository append/publish helper ownership and attach eager publish wrappers.
- The boundary test asserts the current generic outbox wrapper shape used by session transitions.
- The test remains strict enough to catch accidental reintroduction of repository-owned outbox publish wrappers.

## Subproblems
- none

## Results
- R296

## Latest Check
C313

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P316/README.md
- Ticket T304: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P316/tickets/T304.md
- Result R296: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P316/results/R296.md
- Check C313: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/children/P310/children/P312/children/P314/children/P316/checks/C313.md

## Follow-ups
- none
