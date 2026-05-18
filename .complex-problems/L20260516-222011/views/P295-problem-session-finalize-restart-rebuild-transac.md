# P295: Problem: Session finalize restart rebuild transaction flow audit

Status: done
Parent: P292
Root: P000
Source Ticket: T282 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P295
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P295/README.md
Ticket(s): T290

## Problem
Audit session finalize/session_ended, pending restart, suspected-dead recovery, and startup rebuild flows for generation correctness and state mutation ownership.

## Success Criteria
- Map finalize/restart/rebuild branches and transaction boundaries with file references.
- Identify whether stale finalize/restart paths can mutate current state.
- Flag any duplicated state mutation outside the ledger boundary.

## Subproblems
- P303: Session finalize transaction flow audit
- P304: Session restart transaction flow audit
- P305: Session rebuild projection transaction flow audit

## Results
- R291

## Latest Check
C308

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P295/README.md
- Ticket T290: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P295/tickets/T290.md
- Result R291: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P295/results/R291.md
- Check C308: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P295/checks/C308.md

## Follow-ups
- none
