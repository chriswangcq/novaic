# P294: Problem: Session dispatch transaction flow audit

Status: done
Parent: P292
Root: P000
Source Ticket: T282 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P294
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P294/README.md
Ticket(s): T283

## Problem
Audit `SessionRepository.dispatch()` from input append through FSM decision, state transition, outbox effect creation, and return values.

## Success Criteria
- Map dispatch branches and transaction boundaries with file references.
- Identify whether start/attach/buffer paths all use explicit FSM and ledger/outbox effects.
- Flag any direct publish or state mutation inside the wrong boundary.

## Subproblems
- P297: Problem: Unify dispatch start-wake transition construction

## Results
- R277

## Latest Check
C299

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P294/README.md
- Ticket T283: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P294/tickets/T283.md
- Result R277: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P294/results/R277.md
- Check C292: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P294/checks/C292.md
- Check C299: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P292/children/P294/checks/C299.md

## Follow-ups
- P297: Problem: Unify dispatch start-wake transition construction
