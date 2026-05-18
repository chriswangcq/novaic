# P352: Runtime finalize enforcement aggregate verification

Status: done
Parent: P337
Root: P000
Source Ticket: T336 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P352
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P352/README.md
Ticket(s): T354

## Problem
After P337 implementation children complete, run an aggregate verification that stale/missing runtime finalize identity cannot mutate Cortex, session state, or pending inbox, while valid finalize still works.

## Success Criteria
- Run focused tests across react contracts, cortex handlers, session-ended delivery, repository finalize, recovery/compensation, and pending restart.
- Run source guards for `session_generation or 0` in finalize-producing runtime paths.
- Record residual risks and follow-ups if any mutation path remains only partially guarded.

## Subproblems
- none

## Results
- R348

## Latest Check
C370

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P352/README.md
- Ticket T354: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P352/tickets/T354.md
- Result R348: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P352/results/R348.md
- Check C370: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P352/checks/C370.md

## Follow-ups
- none
