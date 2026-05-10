# P050: Migrate hooks and metrics lifecycle tests

Status: done
Parent: P047
Root: P000
Package: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050
Body: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/README.md
Ticket(s): T045

## Problem
Hook and metric tests are coupled to removed runtime lifecycle helpers. Some assertions may represent obsolete runtime-hook behavior rather than live event-wired lifecycle behavior, so this family needs careful rewrite or deletion rather than compatibility restoration.

## Success Criteria
- `tests/test_hooks_metrics.py`, `tests/test_hooks_limits.py`, and `tests/test_wave4_metrics.py` no longer call `cortex.scope_create(...)` or `cortex.scope_end(...)`.
- Obsolete runtime lifecycle hook assertions are removed or replaced with relevant runtime/tool/API-facing coverage.
- Focused hooks/metrics tests pass.

## Subproblems
- P052: Rewrite hook tests to Workspace projection emitter
- P053: Remove dead runtime scope lifecycle metrics coverage

## Results
- R042

## Latest Check
C045

## Bodies
- Problem: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/README.md
- Ticket T045: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/tickets/T045.md
- Result R042: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/results/R042.md
- Check C045: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/checks/C045.md

## Follow-ups
- none
