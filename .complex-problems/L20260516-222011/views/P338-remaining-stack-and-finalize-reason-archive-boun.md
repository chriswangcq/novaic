# P338: Remaining stack and finalize reason archive boundary

Status: done
Parent: P328
Root: P000
Source Ticket: T324 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/README.md
Ticket(s): T355

## Problem
Finalize/session-ended events must record why a wake ended and what stack remained at the same generation boundary. If reason or remaining stack is recorded separately from generation checks, diagnostics and recovery can point at the wrong wake.

## Success Criteria
- Map where finalize reason, ended-at, and remaining stack are recorded.
- Verify these records are tied to explicit saga/scope/generation identity.
- Fix any path that records reason or remaining stack based on stale active lookup after generation changed.
- Add tests proving stale finalize cannot archive remaining stack for a newer wake.
- Add tests proving valid finalize records reason and remaining stack for the intended generation.

## Subproblems
- P366: Child Problem: Finalize Diagnostics Source Map
- P367: Child Problem: Session Finalize Diagnostics Binding
- P368: Child Problem: Cortex Archive Diagnostics Binding
- P369: Child Problem: Finalize Diagnostics Aggregate Verification

## Results
- R362

## Latest Check
C385

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/README.md
- Ticket T355: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/tickets/T355.md
- Result R362: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/results/R362.md
- Check C385: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P338/checks/C385.md

## Follow-ups
- none
