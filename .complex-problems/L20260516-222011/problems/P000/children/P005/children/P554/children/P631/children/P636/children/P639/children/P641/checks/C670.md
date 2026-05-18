# P641 Workspace and Authority RW Fixture Rewrite Check

## Summary

Success. The targeted workspace/authority test fixtures no longer use root `/rw/scratch`, and the original write/read/tree/key-mapping invariants remain covered by passing tests.

## Evidence

- `.complex-problems/L20260516-222011/tmp/p641-scan.txt`: no `/rw/scratch` remains in `test_workspace.py`, `test_workspace_limits.py`, or `test_workspace_authority.py`.
- `.complex-problems/L20260516-222011/tmp/p641-tests.txt`: 22 tests passed.
- R629 lists each touched file and the new neutral `/rw/tmp` paths.

## Criteria Map

- Updates listed workspace/authority root scratch fixtures: satisfied.
- Preserves missing path, binary IO, tree listing, append/read, and key mapping assertions: satisfied by focused tests.
- Runs focused tests: satisfied.

## Execution Map

- T635 marked executing.
- Rewrote three test files.
- Ran scan and focused tests.
- Recorded R629.

## Stress Test

The tree listing test no longer depends on the old initialized `.keep`; this specifically checks the risk introduced by P638 removing `/rw/scratch` initialization.

## Residual Risk

Remaining Cortex `/rw/scratch` hits are owned by P642/P643.

## Result IDs

- R629
