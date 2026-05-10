# P019: Phase 3C Runtime Stack Read And LIFO Cutover

Status: done
Parent: P004
Root: P000
Package: problems/P000/children/P004/children/P019
Body: problems/P000/children/P004/children/P019/README.md
Ticket(s): T025

## Problem
Runtime stack reads and LIFO mismatch checks still rely on file-walk projection. They must use operational SQLite projection as the control-plane authority.

## Success Criteria
- `context_status` reads default stack frames from SQLite active-stack projection.
- `skill_begin` determines parent/top scope from SQLite, not `_collect_active_stack`.
- `skill_end` validates current top scope from SQLite, not `_collect_active_stack`.
- Structured mismatch and empty-stack errors preserve existing API semantics.
- Tests cover wrong-scope close, stack-empty behavior, and open-child behavior after a fresh registry/workspace instance.

## Subproblems
- P030: Phase 3C1 SQLite Active Stack Read Adapter
- P031: Phase 3C2 Context Status SQLite Stack Read Cutover
- P032: Phase 3C3 Skill Begin Parent Selection SQLite Cutover
- P033: Phase 3C4 Skill End LIFO SQLite Cutover
- P034: Phase 3C5 Runtime Read Cutover Verification Gate

## Results
- R028

## Latest Check
C030

## Bodies
- Problem: problems/P000/children/P004/children/P019/README.md
- Ticket T025: problems/P000/children/P004/children/P019/tickets/T025.md
- Result R028: problems/P000/children/P004/children/P019/results/R028.md
- Check C030: problems/P000/children/P004/children/P019/checks/C030.md

## Follow-ups
- none
