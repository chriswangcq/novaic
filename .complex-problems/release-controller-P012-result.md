# P012 Result

## Summary

Implemented branch head polling for the release-controller core and refactored release execution into a shared executor used by both API and poller paths.

## Changes

- Added `release_controller.poller`.
- Added `BranchHead`, `BranchHeadProvider`, `GitBranchHeadProvider`, `InMemoryBranchHeadProvider`, `BranchPoller`, and `parse_ls_remote_heads`.
- Added changed-head detection against `ReleaseStateStore.read_branch_heads()`.
- Added poll-triggered planning with `TriggerKind.POLL`.
- Added unchanged and unmatched branch skip outcomes.
- Added poll-triggered prod-resolution guard through the existing planner.
- Added `release_controller.executor.execute_planned_release` and updated HTTP service endpoints to reuse it.
- Exported poller types from the package.
- Added poller unit tests.

## Verification

- `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q`
  - Passed: 31 tests.
- `PYTHONPATH=novaic-release-controller python3 - <<'PY' ...`
  - Confirmed `BranchHead`, `BranchPoller`, and `InMemoryBranchHeadProvider` imports.

## Notes

- The poller is synchronous and single-iteration by design. A later deployment integration can run it on a timer or call it from a controller loop without changing the core behavior.
