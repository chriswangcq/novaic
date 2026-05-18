# P297: Problem: Unify dispatch start-wake transition construction

Status: done
Parent: P294
Root: P000
Source Ticket: none (none)
Source Check: C292
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P294/children/P297
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P294/children/P297/README.md
Ticket(s): T284

## Problem
`SessionRepository.dispatch()` has two active implementations for building and recording start-wake durable outbox transitions: ordinary no-active start inside the initial transaction and recovery start after the initial transaction. Both are currently durable, but duplicated construction risks future drift.

## Success Criteria
- Extract or otherwise unify the shared start-wake transition construction/recording logic so ordinary start and recovery start cannot diverge silently.
- Preserve durable outbox authority and required outbox checks.
- Preserve input consumption and recovery archive behavior.
- Add or update focused tests/guards that would fail if duplicate active start-wake construction returns.

## Subproblems
- P298: Problem: Dispatch start-wake helper design
- P299: Problem: Dispatch start-wake helper implementation
- P300: Problem: Dispatch start-wake helper verification

## Results
- R283

## Latest Check
C298

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P294/children/P297/README.md
- Ticket T284: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P294/children/P297/tickets/T284.md
- Result R283: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P294/children/P297/results/R283.md
- Check C298: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P294/children/P297/checks/C298.md

## Follow-ups
- none
