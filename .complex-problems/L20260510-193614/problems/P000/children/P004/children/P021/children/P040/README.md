# Delete Or Isolate Workspace Active Path File-Walk Helper

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
