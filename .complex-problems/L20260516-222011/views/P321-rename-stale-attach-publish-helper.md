# P321: Rename stale attach publish helper

Status: done
Parent: P319
Root: P000
Source Ticket: none (none)
Source Check: C322
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P319/children/P321
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P319/children/P321/README.md
Ticket(s): T310

## Problem
`SessionRepository._publish_attach_request_after_transaction(...)` no longer publishes an external effect. It records an attach transition and durable outbox effect, then returns outbox-pending metadata. The stale name can mislead future changes back toward repository-owned delivery.

## Success Criteria
- Rename `_publish_attach_request_after_transaction` to a term that reflects durable attach transition/outbox recording.
- Update all call sites and tests/source guards if needed.
- Confirm no production method name still suggests repository-owned attach publish.
- Run focused attach/boundary tests or source guards sufficient for the rename.

## Subproblems
- none

## Results
- R304

## Latest Check
C323

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P319/children/P321/README.md
- Ticket T310: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P319/children/P321/tickets/T310.md
- Result R304: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P319/children/P321/results/R304.md
- Check C323: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P319/children/P321/checks/C323.md

## Follow-ups
- none
