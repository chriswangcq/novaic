# P004: Phase 3 Active Stack And Status SQLite Cutover

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): T014

## Problem
Runtime active stack/status still reads projection files. Switch control stack authority to SQLite projection.

## Success Criteria
- `skill_begin`, `skill_end`, and `context_status` read/write stack projection from SQLite.
- Projection-file walking is removed from the runtime authority path or isolated as repair/debug only.
- Tests cover nesting, mismatch, finalize/open-child behavior, restart recovery, and old path residue.

## Subproblems
- P017: Phase 3A Active Stack Authority Audit
- P018: Phase 3B SQLite Active Stack Write Projection
- P019: Phase 3C Runtime Stack Read And LIFO Cutover
- P020: Phase 3D Quarantine File-Walk Stack Authority
- P021: Phase 3E Active Stack Cutover Verification

## Results
- R037

## Latest Check
C040

## Bodies
- Problem: problems/P000/children/P004/README.md
- Ticket T014: problems/P000/children/P004/tickets/T014.md
- Result R037: problems/P000/children/P004/results/R037.md
- Check C040: problems/P000/children/P004/checks/C040.md

## Follow-ups
- none
