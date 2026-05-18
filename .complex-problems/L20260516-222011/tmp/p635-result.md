# RW Scratch Usage Inventory Result

## Summary

Completed read-only inventory of root `/rw/scratch` usage. The current intended shell contract is subagent-aware `RW_SCRATCH=/cortex/rw/subagents/{id}/scratch`; root `/rw/scratch` remains as Workspace initialization residue and many Cortex tests use it as a generic writable fixture path.

## Done

- Recorded exact scans in `.complex-problems/L20260516-222011/tmp/p635/scratch-scan.txt`.
- Captured slices for Workspace layout, Cortex LogicalFS layout, LogicalFS tests, and Cortex tests.
- Classified hits in `.complex-problems/L20260516-222011/tmp/p635/classification.md`.

## P636 Targets

- Remove `/rw/scratch` from `Workspace.initialize()` default layout.
- Update `test_initialize_creates_layout` and Cortex tests currently using root `/rw/scratch` as generic fixture paths.
- Preserve current `RW_SCRATCH=/rw/subagents/{id}/scratch` behavior in `logical_fs.py` and `test_sandboxd_wiring.py`.
- Leave lower-layer `novaic-logicalfs` generic path tests unchanged unless P636 proves they encode Cortex semantics.

## Verification

This ticket was read-only; verification is the exact scans and classification artifacts.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p635/scratch-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p635/classification.md`
- `.complex-problems/L20260516-222011/tmp/p635/workspace-layout-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p635/cortex-logicalfs-rw-layout-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p635/cortex-test-slices.txt`
- `.complex-problems/L20260516-222011/tmp/p635/logicalfs-tests-slice.txt`
