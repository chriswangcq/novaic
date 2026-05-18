# P381: Runtime focused finalize regression tests

Status: done
Parent: P378
Root: P000
Source Ticket: T369 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/children/P381
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/children/P381/README.md
Ticket(s): T370

## Problem
The runtime finalize/session-ended generation boundary needs a focused pytest pass covering the actual state mutation and outbox/recovery paths.

## Success Criteria
- Focused runtime modules compile successfully.
- Focused runtime pytest suites for finalize ownership, session FSM, recovery, outbox cutover, attach/dispatch, and compensation pass.
- Any failing or missing runtime test is fixed or split into a follow-up problem.
- The result records exact commands and outcomes.

## Subproblems
- none

## Results
- R363

## Latest Check
C386

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/children/P381/README.md
- Ticket T370: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/children/P381/tickets/T370.md
- Result R363: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/children/P381/results/R363.md
- Check C386: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P378/children/P381/checks/C386.md

## Follow-ups
- none
