# Migrate Tests And Prove Cortex Cutover

## Problem Definition

The code path is being cut to LogicalFS authority, but many tests still instantiate the old direct constructors. If these remain, they either fail or pressure the runtime to keep compatibility branches. P028 must migrate tests and prove shell/API behavior through the new boundary.

## Proposed Solution

Split test migration into smaller child problems: migrate remaining direct Workspace constructor tests, migrate direct Cortex constructor tests, then run full targeted and canonical verification with residue scans. Do not reintroduce old constructors for test convenience.

## Acceptance Criteria

- Tests no longer use `Workspace(MemoryStore(), ...)` or `Cortex(MemoryStore(), ...)` direct live constructor patterns.
- Runtime/API/sandbox tests create Workspaces through explicit LogicalFS-backed helpers.
- Full Cortex tests pass.
- Shell RO/RW materialization and RW patch persistence tests pass.
- Residue scans show no old direct constructor or old authority imports in active tests, except isolated object-store tests.

## Verification Plan

- Split into child tickets for Workspace-style tests, Cortex runtime-style tests, and final verification.
- Run targeted tests after each migration slice.
- Run full Cortex suite and source scans before checking success.

## Risks

- Mechanical replacements can hide a bad helper if not tested behaviorally.
- Some tests legitimately test `MemoryStore` / `LocalFileStore` object stores; residue scans must distinguish object-store unit tests from live Workspace/Cortex construction.

## Assumptions

- `tests/workspace_test_utils.py` is the intended shared testing seam for live Workspace construction.
