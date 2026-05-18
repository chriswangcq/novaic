# P635 RW Scratch Usage Inventory Check

## Summary

Success. The one-go inventory is read-only, records exact scans/slices, and clearly separates current subagent-aware scratch behavior from removable Cortex root scratch layout and generic test fixtures.

## Evidence

- `.complex-problems/L20260516-222011/tmp/p635/scratch-scan.txt` records exact scans for `/rw/scratch`, `RW_SCRATCH`, `/rw/subagents`, `initialize_layout`, and writable env terms.
- `.complex-problems/L20260516-222011/tmp/p635/workspace-layout-slice.txt` shows Workspace still initializes `/rw/scratch`.
- `.complex-problems/L20260516-222011/tmp/p635/cortex-logicalfs-rw-layout-slice.txt` shows intended `RW_SCRATCH=/rw/subagents/{id}/scratch`.
- `.complex-problems/L20260516-222011/tmp/p635/classification.md` lists exact P636 edit targets and out-of-scope LogicalFS generic tests.

## Criteria Map

- Records exact scans: satisfied.
- Classifies every relevant hit category: satisfied.
- Produces exact P636 edit target list: satisfied.
- No code changed: satisfied.

## Execution Map

- T631 was marked executing.
- Static scans and slices were recorded under `.complex-problems/L20260516-222011/tmp/p635/`.
- R627 recorded the result and edit target list.

## Stress Test

The check guards against two opposite mistakes: leaving Workspace's default `/rw/scratch` initialization in place, and over-deleting lower-layer LogicalFS tests that only prove arbitrary path behavior. The classification distinguishes both.

## Residual Risk

Implementation remains for P636. No P635 follow-up is needed.

## Result IDs

- R627
