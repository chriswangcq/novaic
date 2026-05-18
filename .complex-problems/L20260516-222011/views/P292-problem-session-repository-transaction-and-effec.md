# P292: Problem: Session repository transaction and effect orchestration inventory

Status: done
Parent: P287
Root: P000
Source Ticket: T280 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/README.md
Ticket(s): T282

## Problem
Inspect `SessionRepository` write paths to understand transaction grouping, FSM decision usage, outbox creation, input consumption, and any publish-after-transaction behavior.

## Success Criteria
- Map dispatch/finalize/restart/rebuild write flows with file references.
- Identify which writes happen inside global DB transactions and which publishes happen after transaction.
- Flag any hidden or duplicated state mutation path.

## Subproblems
- P294: Problem: Session dispatch transaction flow audit
- P295: Problem: Session finalize restart rebuild transaction flow audit
- P296: Problem: Session after-transaction publish and outbox boundary audit

## Results
- R301

## Latest Check
C320

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/README.md
- Ticket T282: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/tickets/T282.md
- Result R301: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/results/R301.md
- Check C320: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/checks/C320.md

## Follow-ups
- none
