# P284: Problem: Session outbox side-effect ownership audit

Status: done
Parent: P278
Root: P000
Source Ticket: T275 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P284
Body: problems/P000/children/P004/children/P278/children/P284/README.md
Ticket(s): T450

## Problem
Audit whether wake saga creation, attach-input publishing, recovery archive publishing, and observed wake-created updates are owned by durable outbox rows and idempotent handlers rather than direct ad hoc side effects.

## Success Criteria
- Map session outbox effect types and handlers with file references.
- Identify whether any session side effect bypasses durable outbox ownership.
- Classify remaining direct calls as safe implementation details, risky, or removable.

## Subproblems
- P458: Session outbox effect inventory
- P459: Session direct side-effect bypass classification
- P460: Session outbox ownership final verification

## Results
- R454

## Latest Check
C481

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P284/README.md
- Ticket T450: problems/P000/children/P004/children/P278/children/P284/tickets/T450.md
- Result R454: problems/P000/children/P004/children/P278/children/P284/results/R454.md
- Check C481: problems/P000/children/P004/children/P278/children/P284/checks/C481.md

## Follow-ups
- none
