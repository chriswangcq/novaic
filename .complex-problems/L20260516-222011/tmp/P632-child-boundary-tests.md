# LogicalFS Sandbox Boundary Focused Verification

## Problem

After residue audits, focused tests must verify that the intended LogicalFS/sandbox boundary still works and no fallback cleanup broke shell/workspace behavior.

## Success Criteria

- Runs focused Cortex LogicalFS/workspace/sandbox/runtime boundary tests.
- Runs relevant LogicalFS/sandbox service tests if audit touches those layers.
- Records commands and outputs.
- Converts failures into follow-up problems instead of ignoring them.
