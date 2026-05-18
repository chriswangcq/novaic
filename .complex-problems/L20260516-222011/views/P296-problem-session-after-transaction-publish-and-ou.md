# P296: Problem: Session after-transaction publish and outbox boundary audit

Status: done
Parent: P292
Root: P000
Source Ticket: T282 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/README.md
Ticket(s): T298

## Problem
Audit helper methods that publish attach or wake/recovery outbox effects after DB transactions. Confirm durable outbox rows remain the authority even when a synchronous publish path returns task IDs to callers.

## Success Criteria
- Map publish-after-transaction helper methods with file references.
- Confirm side effects are backed by durable outbox rows and idempotency keys.
- Flag any direct side effect that bypasses outbox durability.

## Subproblems
- P310: Remove repository eager attach publish

## Results
- R292

## Latest Check
C319

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/README.md
- Ticket T298: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/tickets/T298.md
- Result R292: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/results/R292.md
- Check C309: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/checks/C309.md
- Check C319: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P296/checks/C319.md

## Follow-ups
- P310: Remove repository eager attach publish
