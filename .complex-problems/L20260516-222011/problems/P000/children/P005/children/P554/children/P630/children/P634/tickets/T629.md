# Remove Workspace.materialize and Its Stale Test Contract

## Problem Definition

P633 proved that the stale direct materialization contract is isolated to `Workspace.materialize()` in `novaic_cortex.workspace` and `tests/test_workspace_materialize.py`. The method writes to global `/rw/scratch`, which is not the intended LogicalFS/sandboxd file-view boundary.

## Proposed Solution

Delete `Workspace.materialize()` from `workspace.py` and remove `tests/test_workspace_materialize.py` if no current behavior remains to rewrite. Keep LogicalFS provider materialization untouched. Add or rely on existing tests that protect current LogicalFS/sandboxd behavior, then run focused tests and post-change scans.

## Acceptance Criteria

- `Workspace.materialize()` and direct `/rw/scratch` test contract are removed.
- Legitimate LogicalFS materialization code remains intact.
- Post-change scans show no `Workspace.materialize`, `def materialize` in `workspace.py`, or `test_workspace_materialize.py` stale dependency remains.
- Focused Cortex tests pass.

## Verification Plan

Run post-change `rg` scans for `Workspace.materialize`, `def materialize`, `.materialize(`, and `/rw/scratch`; run focused `pytest` suites for Cortex workspace/logicalfs/sandbox wiring and any tests affected by file deletion.

## Risks

- Removing a test file reduces line count but could remove validation of filename safety; that safety belonged only to the deleted stale API.
- Broad `materialize` hits in LogicalFS must not be edited.

## Assumptions

- P633 classification is correct and complete.
- Deleting stale test contract is preferred over preserving compatibility behavior.
