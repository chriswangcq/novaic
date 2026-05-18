# Workspace Materialize Reference Inventory Result

## Summary

Completed read-only reference inventory for `Workspace.materialize()`. The stale API is confined to `novaic_cortex.workspace.Workspace.materialize` and `tests/test_workspace_materialize.py`. Broad `materialize` hits include intended LogicalFS substrate materialization and unrelated context projection terminology, which P634 should not delete.

## Done

- Recorded exact scan commands and outputs in `.complex-problems/L20260516-222011/tmp/p633/materialize-scan.txt`.
- Captured source slices in:
  - `.complex-problems/L20260516-222011/tmp/p633/workspace-materialize-slice.txt`
  - `.complex-problems/L20260516-222011/tmp/p633/test-workspace-materialize-slice.txt`
  - `.complex-problems/L20260516-222011/tmp/p633/logicalfs-materialize-slice.txt`
- Classified hits in `.complex-problems/L20260516-222011/tmp/p633/classification.md`.

## P634 Targets

- Remove `Workspace.materialize()` from `novaic-cortex/novaic_cortex/workspace.py`.
- Delete or rewrite `novaic-cortex/tests/test_workspace_materialize.py` because it protects the stale `/rw/scratch` materialize contract.
- Preserve `logical_fs.py` provider materialization and context projection terminology/tests.

## Verification

This ticket was read-only. Verification is the recorded exact scans and source slices.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p633/materialize-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p633/classification.md`
