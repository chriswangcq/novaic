# P507: Finalize and recovery ownership map

Status: done
Parent: P280
Root: P000
Source Ticket: T502 (split)
Source Check: none
Package: problems/P000/children/P004/children/P280/children/P507
Body: problems/P000/children/P004/children/P280/children/P507/README.md
Ticket(s): T503

## Problem
P280 needs a concrete map of normal finalize, suspected-dead/watchdog, recovery archive, recovery wake creation, and remaining-stack archival paths before any ownership claim can be trusted.

## Success Criteria
- Code paths are mapped with file references and brief flow descriptions.
- The map identifies the owner for each side effect: FSM decision, session ledger, session outbox, saga compensation, Cortex archive, or worker boundary.
- Any ambiguous or multi-owner path is listed as a candidate for the remediation child.
- No production code is changed in this mapping child.

## Subproblems
- none

## Results
- R500

## Latest Check
C529

## Bodies
- Problem: problems/P000/children/P004/children/P280/children/P507/README.md
- Ticket T503: problems/P000/children/P004/children/P280/children/P507/tickets/T503.md
- Result R500: problems/P000/children/P004/children/P280/children/P507/results/R500.md
- Check C529: problems/P000/children/P004/children/P280/children/P507/checks/C529.md

## Follow-ups
- none
