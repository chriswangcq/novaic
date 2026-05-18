# P496: Attach generation contract inventory

Status: done
Parent: P490
Root: P000
Source Ticket: T487 (split)
Source Check: none
Package: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P496
Body: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P496/README.md
Ticket(s): T488

## Problem
Before changing attach code, inventory all active input attach paths and classify whether they require explicit expected wake scope and expected session generation. This belongs under P490 because attach race buffering is legitimate, while no-generation delivery is not.

## Success Criteria
- Runtime attach handler, session outbox publisher, attach effect builder, and session repo attach-race handling are inspected.
- Raw and classified artifacts are saved.
- Any missing or ambiguous attach-generation contract becomes a child/follow-up instead of being waved away.

## Subproblems
- none

## Results
- R483

## Latest Check
C512

## Bodies
- Problem: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P496/README.md
- Ticket T488: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P496/tickets/T488.md
- Result R483: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P496/results/R483.md
- Check C512: problems/P000/children/P004/children/P279/children/P482/children/P490/children/P496/checks/C512.md

## Follow-ups
- none
