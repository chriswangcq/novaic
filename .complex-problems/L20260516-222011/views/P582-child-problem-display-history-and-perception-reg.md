# P582: Child Problem: Display history and perception regression test inventory

Status: done
Parent: P575
Root: P000
Source Ticket: T572 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/README.md
Ticket(s): T584

## Problem
Audit tests that protect display media handling, including current-turn image injection, text-only history replay, active-stack ordering, and absence of raw base64 in durable tool text.

## Success Criteria
- Records exact test scan commands and test slices.
- Maps each display-media invariant to at least one existing test or a follow-up.
- Classifies missing or weak test coverage.
- Forwards concrete test gaps to P554 or the aggregate verification ticket as appropriate.

## Subproblems
- P593: Current Display Image Injection Test Coverage
- P594: Historical Display Replay Text-Only Test Coverage
- P595: Durable Shell and Display Output Base64 Absence Test Coverage
- P596: Active Stack and System Message Display Ordering Test Coverage

## Results
- R586

## Latest Check
C624

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/README.md
- Ticket T584: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/tickets/T584.md
- Result R586: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/results/R586.md
- Check C624: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P582/checks/C624.md

## Follow-ups
- none
