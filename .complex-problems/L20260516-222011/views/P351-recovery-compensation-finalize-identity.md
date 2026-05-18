# P351: Recovery compensation finalize identity

Status: done
Parent: P337
Root: P000
Source Ticket: T336 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/README.md
Ticket(s): T348

## Problem
Recovery and compensation paths can synthesize wake-finalize contexts after failures. They must preserve or require explicit session generation and wake scope identity rather than creating ambiguous finalize tasks.

## Success Criteria
- Inspect `queue_service/saga_repo.py`, `queue_service/session_recovery.py`, recovery tests, and compensation tests.
- Verify compensation-created `wake_finalize` contexts carry positive session generation when the failed saga had one.
- Ensure missing generation in compensation/recovery is either rejected or explicitly routed to a dead-session/recovery path without mutating a newer active session.
- Add or update tests for compensation/recovery generation preservation.

## Subproblems
- P361: Recovery compensation finalize source map
- P362: Compensation wake_finalize generation preservation
- P363: Session recovery missing identity handling
- P364: Recovery compensation finalize aggregate verification

## Results
- R347

## Latest Check
C369

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/README.md
- Ticket T348: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/tickets/T348.md
- Result R347: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/results/R347.md
- Check C369: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/checks/C369.md

## Follow-ups
- none
