# P002 Not Success Check

## Summary

P002 is not fully successful yet. The core service now has config, state, planner, runner, HTTP APIs, and tests, but it does not yet implement branch head polling. The original problem explicitly included polling branch heads, so this must be closed before the release-controller core can be considered complete.

## Blocking Gaps

- Missing branch head polling loop that checks configured branch rules against the git remote or worktree.
- Missing changed-head detection that updates `branch-heads.json`.
- Missing poll-triggered non-prod release planning path that reuses the existing planner and runner.
- Missing tests proving unchanged heads are skipped and changed heads create a dry-run or executable plan.

## Result IDs

- R006
