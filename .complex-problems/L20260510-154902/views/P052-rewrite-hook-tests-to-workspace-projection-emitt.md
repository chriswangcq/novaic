# P052: Rewrite hook tests to Workspace projection emitter

Status: done
Parent: P050
Root: P000
Package: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/children/P052
Body: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/children/P052/README.md
Ticket(s): T046

## Problem
Hook tests currently call removed runtime lifecycle helpers even though `on_scope_created` and `on_scope_archived` are emitted by Workspace lifecycle projection methods. They should test the emitter directly without runtime bypasses.

## Success Criteria
- `tests/test_hooks_metrics.py` and hook-focused cases in `tests/test_hooks_limits.py` no longer call `cortex.scope_create(...)` or `cortex.scope_end(...)`.
- Hook success/failure/isolation behavior is still covered using Workspace lifecycle/projection methods.
- Focused hook tests pass.

## Subproblems
- none

## Results
- R040

## Latest Check
C043

## Bodies
- Problem: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/children/P052/README.md
- Ticket T046: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/children/P052/tickets/T046.md
- Result R040: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/children/P052/results/R040.md
- Check C043: problems/P000/children/P004/children/P028/children/P043/children/P047/children/P050/children/P052/checks/C043.md

## Follow-ups
- none
