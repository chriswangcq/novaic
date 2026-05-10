# P051: Migrate miscellaneous runtime lifecycle tests

Status: done
Parent: P047
Root: P000
Package: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P051
Body: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P051/README.md
Ticket(s): T048

## Problem
Miscellaneous tests still use runtime lifecycle helpers for setup or convenience. They must be moved to API/projection setup or rewritten so the runtime bypass is not preserved.

## Success Criteria
- `tests/test_engine_wiring.py`, `tests/test_compaction_meta.py`, and `tests/test_cortex_chaos.py` no longer call `cortex.scope_create(...)` or `cortex.scope_end(...)`.
- Each migrated test still asserts its original non-obsolete behavior.
- Focused miscellaneous migrated tests pass.

## Subproblems
- none

## Results
- R043

## Latest Check
C046

## Bodies
- Problem: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P051/README.md
- Ticket T048: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P051/tickets/T048.md
- Result R043: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P051/results/R043.md
- Check C046: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P051/checks/C046.md

## Follow-ups
- none
