# P287: Problem: Session repository state mutation inventory

Status: done
Parent: P282
Root: P000
Source Ticket: T276 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P287
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/README.md
Ticket(s): T280

## Problem
Inspect SessionRepository and SessionLedgerRepository write paths to identify all code that mutates session state, input events, pending projections, and outbox rows.

## Success Criteria
- List mutation methods and their target tables/effects with file references.
- Identify whether writes are grouped in explicit transactions.
- Flag any state mutation outside session ledger/repository boundaries.

## Subproblems
- P291: Problem: Session ledger mutation API inventory
- P292: Problem: Session repository transaction and effect orchestration inventory
- P293: Problem: Session direct SQL and mutation residue scan

## Results
- R307

## Latest Check
C327

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/README.md
- Ticket T280: problems/P000/children/P004/children/P278/children/P282/children/P287/tickets/T280.md
- Result R307: problems/P000/children/P004/children/P278/children/P282/children/P287/results/R307.md
- Check C327: problems/P000/children/P004/children/P278/children/P282/children/P287/checks/C327.md

## Follow-ups
- none
