# P040: Delete Or Isolate Workspace Active Path File-Walk Helper

Status: done
Parent: P021
Root: P000
Package: problems/P000/children/P004/children/P021/children/P040
Body: problems/P000/children/P004/children/P021/children/P040/README.md
Ticket(s): T038

## Problem
`novaic-cortex/novaic_cortex/workspace.py` still defines `Workspace.resolve_active_scope_path(...)`, which walks `steps/_index.jsonl` scope entries to find the deepest active scope. Live `api.py` no longer calls it, but this lower-level helper remains stack-related file-walk residue without explicit repair/debug isolation.

This violates the Phase 3E criterion that remaining stack-related file projection code must be documented as trace/repair/debug, not runtime authority. Given the user's no-compat/no-residue principle, the preferred solution is physical deletion if no live callers remain.

## Success Criteria
- All live references to `Workspace.resolve_active_scope_path(...)` are audited.
- If no live callers remain, `Workspace.resolve_active_scope_path(...)` is deleted from `workspace.py`.
- If any non-runtime caller truly needs it, it is renamed to an explicit repair/debug helper and documented as non-authoritative.
- Tests are updated so no test depends on the old helper name for runtime behavior.
- Static search proves no unclassified `resolve_active_scope_path` residue remains.
- Targeted tests, full Cortex tests, and `py_compile` pass.

## Subproblems
- none

## Results
- R036

## Latest Check
C038

## Bodies
- Problem: problems/P000/children/P004/children/P021/children/P040/README.md
- Ticket T038: problems/P000/children/P004/children/P021/children/P040/tickets/T038.md
- Result R036: problems/P000/children/P004/children/P021/children/P040/results/R036.md
- Check C038: problems/P000/children/P004/children/P021/children/P040/checks/C038.md

## Follow-ups
- none
