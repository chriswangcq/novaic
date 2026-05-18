# P306: Finalize pending restart atomicity fix

Status: done
Parent: P303
Root: P000
Source Ticket: none (none)
Source Check: C300
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P295/children/P303/children/P306
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P295/children/P303/children/P306/README.md
Ticket(s): T292

## Problem
When `session_ended(...)` accepts finalize and finds pending input, it currently clears active session state to `no_active` in one transaction, then records restart intent/state in a later transaction. A concurrent dispatch can observe `no_active` in the gap and start a competing wake.

## Success Criteria
- Accepted finalize with pending input durably records the restart transition/state without exposing an intermediate externally dispatchable `no_active` gap.
- Durable outbox creation remains required for restart wake creation.
- Generation and pending input consumption semantics remain correct.
- Focused tests cover the race shape or at least assert the restart transition is recorded atomically with finalize decision.

## Subproblems
- P307: Finalize restart atomicity design
- P308: Finalize restart atomicity implementation
- P309: Finalize restart atomicity verification

## Results
- R288

## Latest Check
C304

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P295/children/P303/children/P306/README.md
- Ticket T292: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P295/children/P303/children/P306/tickets/T292.md
- Result R288: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P295/children/P303/children/P306/results/R288.md
- Check C304: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P295/children/P303/children/P306/checks/C304.md

## Follow-ups
- none
