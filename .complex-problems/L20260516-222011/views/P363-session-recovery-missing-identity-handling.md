# P363: Session recovery missing identity handling

Status: done
Parent: P351
Root: P000
Source Ticket: T348 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P363
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P363/README.md
Ticket(s): T351

## Problem
Session recovery paths may reconstruct finalize or dead-session handling from incomplete persisted state. Missing generation or wake scope identity must not be allowed to mutate a newer active session. This belongs under P351 because recovery is the other source of synthesized finalize contexts.

## Success Criteria
- Inspect session recovery behavior for missing `session_generation`, `scope_id`, and wake scope path.
- Ensure incomplete identity is rejected or routed to a clearly non-mutating dead-session/recovery path.
- Add tests for missing generation and stale generation recovery cases.
- Ensure the fix does not recreate old fallback behavior under a different name.

## Subproblems
- none

## Results
- R344

## Latest Check
C365

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P363/README.md
- Ticket T351: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P363/tickets/T351.md
- Result R344: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P363/results/R344.md
- Check C365: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P363/checks/C365.md

## Follow-ups
- none
