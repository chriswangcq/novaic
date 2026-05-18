# P417: Cortex context event lifecycle cleanup

Status: done
Parent: P404
Root: P000
Source Ticket: T405 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/README.md
Ticket(s): T407

## Problem
Cortex context event lifecycle code may still contain generation defaults or compatibility branches that weaken the event-sourced context model.

## Success Criteria
- Inspect live context event API/store/assembly lifecycle hits from the Cortex inventory.
- Remove dangerous defaulting or implicit generation behavior, or replace it with explicit validation.
- Preserve legitimate event projection fields only with explicit classification.
- Add focused tests for any changed context event lifecycle boundary.
- Rerun focused Cortex context event tests.

## Subproblems
- P421: ContextEvent store and writer contract audit
- P422: ContextEvent projection and read-model cleanup
- P423: Workspace step and payload normalization cleanup
- P424: ContextEvent API lifecycle endpoint cleanup
- P425: ContextEvent lifecycle final verification

## Results
- R411

## Latest Check
C437

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/README.md
- Ticket T407: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/tickets/T407.md
- Result R411: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/results/R411.md
- Check C437: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/checks/C437.md

## Follow-ups
- none
