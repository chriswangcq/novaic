# P526 Check: Run Task Saga Worker Focused Pytest

## Summary

Success. The P525 26-file task/saga/worker focused subset was executed from the correct runtime cwd and passed with 124 collected tests.

The initial root-cwd run failed, but that failure was explicitly diagnosed as a cwd contract error and corrected without changing source code.

## Evidence

- Result: `R516`
- Corrected counts: `.complex-problems/L20260516-222011/tmp/p526/task-saga-worker-pytest-corrected-counts.txt`
  - `target_count=26`
  - `pytest_exit=0`
- Corrected pytest log: `.complex-problems/L20260516-222011/tmp/p526/task-saga-worker-pytest-corrected.log`
  - `collected 124 items`
  - `124 passed in 0.98s`
- Target-list equivalence check:
  - `sed 's#^novaic-agent-runtime/##' p525 list` has no diff from `task-saga-worker-test-files.runtime-cwd.txt`.
- Initial root-cwd failure log preserved:
  - `.complex-problems/L20260516-222011/tmp/p526/task-saga-worker-pytest.log`

## Criteria Map

- Pytest runs against exactly the P525 target list: satisfied by the no-diff check after stripping the runtime prefix.
- Command, target count, exit code, and pytest summary saved: satisfied by corrected counts and log artifacts.
- Empty-suite false positive rejected: satisfied by `collected 124 items`.
- Partial-run false positive rejected: target count remains 26 and all selected files appear in the corrected log.
- Failures preserved instead of hidden: initial root-cwd failure is preserved and diagnosed.

## Execution Map

- Tried repository-root execution with P525 project-root paths; it failed with cwd-related source path errors.
- Converted the same P525 list to runtime-cwd paths by stripping `novaic-agent-runtime/`.
- Reran from `novaic-agent-runtime`.
- Verified the corrected run passed.

## Stress Test

- Wrong-cwd risk: exposed by the initial failure and addressed by corrected execution from `novaic-agent-runtime`.
- Wrong-list risk: reduced by diffing the transformed target list against the P525 list.
- Empty-run risk: rejected by 124 collected tests.
- Hidden code-change risk: no production or test source files were modified.

## Residual Risk

P526 proves the task/saga/worker focused subset is green. P527 still needs to audit whether the P525/P526 evidence is sufficient to close P518.

## Result IDs

- `R516`
