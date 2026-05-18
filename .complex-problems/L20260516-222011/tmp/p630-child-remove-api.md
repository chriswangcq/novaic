# Workspace Materialize Removal and Test Rewrite

## Problem

After the reference inventory, remove the stale `Workspace.materialize()` API and rewrite/delete tests that only protect the legacy direct materialization contract.

## Success Criteria

- Removes the stale production API and any test-only dependency on it.
- Preserves legitimate LogicalFS materialization behavior if separate from `Workspace.materialize()`.
- Runs focused tests for edited Cortex workspace/logicalfs code.
- Records post-change scans proving the stale API is gone.
