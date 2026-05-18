# P138: ContextEvent append-only store map

Status: done
Parent: P133
Root: P000
Source Ticket: T123 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P133/children/P138
Body: problems/P000/children/P003/children/P126/children/P133/children/P138/README.md
Ticket(s): T124

## Problem
`ContextEventStore` defines where the event stream lives and how events are appended/read. Its invariants and explicit dependency boundaries must be verified before trusting it as the context source of truth.

## Success Criteria
- Store path, read behavior, append idempotency, sequence assignment, and explicit clock/id provider requirements are documented with source pointers.
- Store tests are identified and run.
- Any hidden input or stale fallback in the store layer is fixed or split into a follow-up.

## Subproblems
- none

## Results
- R120

## Latest Check
C134

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P133/children/P138/README.md
- Ticket T124: problems/P000/children/P003/children/P126/children/P133/children/P138/tickets/T124.md
- Result R120: problems/P000/children/P003/children/P126/children/P133/children/P138/results/R120.md
- Check C134: problems/P000/children/P003/children/P126/children/P133/children/P138/checks/C134.md

## Follow-ups
- none
