# Legacy RW Scratch Layout Cleanup Result

## Summary

Completed classification, cleanup, and final guarding for legacy root `/rw/scratch` in Cortex. Root `/rw/scratch` is no longer created by default or used as the preferred Cortex scratch contract; current scratch behavior is explicitly subagent-aware through LogicalFS execution env.

## Completed Children

- P635 inventoried and classified root scratch usage across Cortex/LogicalFS.
- P636 removed the high-confidence legacy default layout and rewrote Cortex fixtures to neutral/current paths.
- P637 performed the final skeptical guard with fresh scans and focused tests.

## Changes

- Removed `"/rw/scratch"` from `Workspace.initialize()` default layout.
- Rewrote Cortex generic writable test fixtures from root `/rw/scratch` to neutral `/rw/tmp`.
- Preserved and verified current subagent-aware scratch behavior through `/rw/subagents/{id}/scratch` and `RW_SCRATCH=/cortex/rw/subagents/{id}/scratch`.

## Verification

- Inventory/classification completed in P635.
- Cleanup and fixture rewrite completed in P636.
- Final guard completed in P637.
- Latest recorded verification:
  - `.complex-problems/L20260516-222011/tmp/P644-final-rw-scratch-scan.txt`
  - `.complex-problems/L20260516-222011/tmp/P645-cortex-tests.txt`: 88 passed.
  - `.complex-problems/L20260516-222011/tmp/P645-logicalfs-tests.txt`: 9 passed.

## Known Gaps

- LogicalFS lower-layer tests still use root `/rw/scratch` as arbitrary examples. That is intentional lower-layer generic path coverage and not a Cortex default-layout or shell scratch contract.
