# P042: Phase 3.6.1: Mark legacy context/step/lifecycle file writes as projections

Status: done
Parent: P028
Root: P000
Package: problems/P000/children/P004/children/P028/children/P042
Body: problems/P000/children/P004/children/P028/children/P042/README.md
Ticket(s): T040

## Problem
Legacy filesystem writes are still named as generic source writes (`append_context`, `write_step`, `complete_child_scope`), which makes it too easy to mistake them for authoritative state after event cutover.

## Success Criteria
- Active event-wired endpoints call projection-named methods or comments that make legacy writes explicitly non-authoritative.
- Context, step, and skill lifecycle projection writes are distinguishable from event append writes.
- Existing transitional readers/tests continue to pass.
- Static scan can classify remaining write sites by name.

## Subproblems
- none

## Results
- R037

## Latest Check
C040

## Bodies
- Problem: problems/P000/children/P004/children/P028/children/P042/README.md
- Ticket T040: problems/P000/children/P004/children/P028/children/P042/tickets/T040.md
- Result R037: problems/P000/children/P004/children/P028/children/P042/results/R037.md
- Check C040: problems/P000/children/P004/children/P028/children/P042/checks/C040.md

## Follow-ups
- none
