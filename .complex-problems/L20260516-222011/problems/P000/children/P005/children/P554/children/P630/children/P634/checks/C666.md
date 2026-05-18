# P634 Workspace Materialize Removal and Test Rewrite Check

## Summary

Success. The bounded one-go removed the stale `Workspace.materialize()` API and its dedicated stale test contract, preserved legitimate LogicalFS provider materialization, and passed focused tests after correcting the test environment.

## Evidence

- `novaic-cortex/novaic_cortex/workspace.py` no longer contains `Workspace.materialize()`.
- `novaic-cortex/tests/test_workspace_materialize.py` was deleted.
- `.complex-problems/L20260516-222011/tmp/p634-post-change-scan.txt` shows only intended LogicalFS `.materialize(` remains.
- `.complex-problems/L20260516-222011/tmp/p634-focused-tests-rerun.txt` shows 34 passed with the correct monorepo `PYTHONPATH`.

## Criteria Map

- Removes stale production API and test-only dependency: satisfied.
- Preserves legitimate LogicalFS materialization: satisfied; the remaining `logical_fs.py:320` hit is intended provider materialization.
- Runs focused tests: satisfied; 34 passed after environment-correct rerun.
- Records post-change scans: satisfied.

## Execution Map

- T629 was marked executing.
- Removed the stale method and deleted the stale test file.
- Ran post-change scans and focused Cortex workspace/logicalfs/sandbox tests.
- Recorded R625.

## Stress Test

The check validates the two plausible failure modes: accidentally retaining the old `Workspace.materialize()` API, and over-deleting legitimate LogicalFS provider materialization. The scan shows the former is gone and the latter remains.

## Residual Risk

Remaining `/rw/scratch` hits are not waved away; they belong to P631 Legacy RW Scratch Layout Cleanup and must be handled there.

## Result IDs

- R625
