# P529 Check: Run Unit Tool Output Focused Pytest

## Summary

Success. The P528 12-file unit/tool-output/task_queue focused subset was executed from the correct runtime cwd and passed with 47 collected tests.

## Evidence

- Result: `R520`
- Counts: `.complex-problems/L20260516-222011/tmp/p529/unit-tool-output-pytest-counts.txt`
  - `target_count=12`
  - `pytest_exit=0`
- Pytest log: `.complex-problems/L20260516-222011/tmp/p529/unit-tool-output-pytest.log`
  - `collected 47 items`
  - `47 passed in 0.19s`
- Target-list equivalence check:
  - stripping `novaic-agent-runtime/` from P528 list produced no diff against the runtime-cwd list.

## Criteria Map

- Pytest runs against exactly the P519 target list: satisfied by the no-diff target-list check.
- Command, target count, exit code, collected count, and final summary are saved: satisfied.
- Empty-suite false positive rejected: satisfied by `collected 47 items`.
- Failure handling: no failures occurred.

## Execution Map

- Built runtime-cwd target list from P528 project-root target list.
- Ran pytest from `novaic-agent-runtime`.
- Re-read counts and log summary before checking success.

## Stress Test

- Wrong-cwd risk: avoided by using the runtime-cwd list and running from `novaic-agent-runtime`.
- Empty-run risk: rejected by collected test count.
- Wrong-list risk: reduced by no-diff transformation check.

## Residual Risk

P529 only proves the subset ran green. P530 must still audit whether the green subset closes P519.

## Result IDs

- `R520`
