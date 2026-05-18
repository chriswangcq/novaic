# P633 Workspace Materialize Reference Inventory Check

## Summary

Success. The one-go inventory is sufficiently narrow and verified: exact scans are recorded, slices are captured, and each hit is classified with a precise P634 edit target list.

## Evidence

- `.complex-problems/L20260516-222011/tmp/p633/materialize-scan.txt` records exact `rg` commands and outputs.
- `.complex-problems/L20260516-222011/tmp/p633/workspace-materialize-slice.txt` shows `Workspace.materialize()` writes to `/rw/scratch/{filename}`.
- `.complex-problems/L20260516-222011/tmp/p633/test-workspace-materialize-slice.txt` shows the stale test contract asserts `/rw/scratch/image.png`.
- `.complex-problems/L20260516-222011/tmp/p633/logicalfs-materialize-slice.txt` shows `logical_fs.py` provider materialization is intended LogicalFS sandbox plumbing.
- `.complex-problems/L20260516-222011/tmp/p633/classification.md` maps hits to stale API, test-only stale contract, intended LogicalFS internals, and unrelated terminology.

## Criteria Map

- Records exact scans for `Workspace.materialize`, `def materialize`, `.materialize(`, and broad `materialize(`: satisfied.
- Classifies each hit: satisfied.
- Identifies exact implementation targets for P634: satisfied.
- No code changed: satisfied; result is inventory-only.

## Execution Map

- T628 was marked executing.
- Static scans and source slices were written under `.complex-problems/L20260516-222011/tmp/p633/`.
- R624 recorded the result and P634 target list.

## Stress Test

The check specifically guards against over-deletion: broad `materialize` hits include intended LogicalFS provider materialization and context projection terminology, both classified as not P634 targets.

## Residual Risk

No P633 follow-up needed. Implementation risk is intentionally carried into P634.

## Result IDs

- R624
