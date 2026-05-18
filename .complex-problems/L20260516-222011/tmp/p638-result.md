# Workspace Default RW Layout Cleanup Result

## Summary

Removed root `/rw/scratch` from `Workspace.initialize()` default layout and updated the direct initialization test to assert it is not created by default.

## Changes

- `novaic-cortex/novaic_cortex/workspace.py`: removed `"/rw/scratch"` from `initialize_layout(...)`.
- `novaic-cortex/tests/test_workspace.py`: `test_initialize_creates_layout` no longer expects `rw/scratch/.keep` and now asserts it is absent.

## Verification

- `.complex-problems/L20260516-222011/tmp/p638-scan.txt` shows Workspace initialization no longer includes `/rw/scratch`.
- `.complex-problems/L20260516-222011/tmp/p638-tests.txt` shows 2 focused workspace tests passed.

## Known Gaps

- `novaic-cortex/tests/test_workspace.py` still has a generic `/rw/scratch/run.log` fixture; P639 owns broader fixture rewrite.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p638-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p638-tests.txt`
