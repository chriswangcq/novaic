# Cortex Workspace Materialize API Removal

## Problem

`Workspace.materialize()` is stale direct materialization API residue. Even without production callers, it exposes a tempting path around the intended LogicalFS/sandboxd file-view boundary.

## Success Criteria

- Finds all live references to `Workspace.materialize` and `materialize(` in Cortex workspace/logicalfs code and tests.
- Removes `Workspace.materialize()` or reduces it to a non-public non-bypass path only if a current caller proves necessity.
- Rewrites/deletes tests that exist only to preserve the stale materialize contract.
- Runs focused workspace/logicalfs tests affected by the removal.
