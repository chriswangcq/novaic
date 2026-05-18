# P291: Problem: Session ledger mutation API inventory

Status: done
Parent: P287
Root: P000
Source Ticket: T280 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P291
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P291/README.md
Ticket(s): T281

## Problem
Inspect `SessionLedgerRepository` and generic FSM store usage to list all legitimate session event/state/outbox mutation APIs and their explicit dependencies.

## Success Criteria
- List ledger mutation methods and target table/effect categories.
- Verify ID/time inputs are injected at the ledger boundary.
- Identify any ledger method that mixes business decision logic into storage mechanics.

## Subproblems
- none

## Results
- R276

## Latest Check
C291

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P291/README.md
- Ticket T281: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P291/tickets/T281.md
- Result R276: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P291/results/R276.md
- Check C291: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P291/checks/C291.md

## Follow-ups
- none
