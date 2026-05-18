# P566 Result: Cortex Materialize API Residue Classification

## Summary

Classified Cortex materialization and direct file-authority hits. The main risky/removable residue is `Workspace.materialize()` plus the legacy global `/rw/scratch` layout it relies on. No production caller of `Workspace.materialize()` was found; only tests reference it. Direct `_files` access is mostly intended inside the `Workspace` authority wrapper, with one object-key listing path classified as internal implementation rather than a layer bypass.

## Done

- Recorded Cortex scan output:
  - `.complex-problems/L20260516-222011/tmp/p566/materialize-scan.txt`
- Recorded line-numbered source slices:
  - `.complex-problems/L20260516-222011/tmp/p566/materialize-slices.txt`
- Ran focused caller scans:
  - `.materialize(` only appears in `test_workspace_materialize.py` and LogicalFS provider materialization.
  - `self._files.key/list_object_keys` appear in `Workspace.list_active_scopes`.

## Verification

- `Workspace.materialize()` is defined at `novaic-cortex/novaic_cortex/workspace.py:838`.
- It writes to `/rw/scratch/{filename}` at `novaic-cortex/novaic_cortex/workspace.py:850`.
- Global `/rw/scratch` is still initialized at `novaic-cortex/novaic_cortex/workspace.py:1003`.
- Only direct `Workspace.materialize()` callers found are tests in `novaic-cortex/tests/test_workspace_materialize.py`.
- The active LogicalFS shell path uses `MountNamespaceLogicalFS.acquire_view()` and `LocalLogicalFSProvider.materialize()`, which is intended generic materialization rather than `Workspace.materialize()`.

## Known Gaps

- P554 should remove or replace `Workspace.materialize()` and the legacy root `/rw/scratch` layout if no other P553 child proves an active need.
- P554 should update/delete `test_workspace_materialize.py` accordingly.
- Direct `_files` usage inside `Workspace` remains accepted here, but broader Workspace authority cleanup is outside this child.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p566/materialize-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p566/materialize-slices.txt`
