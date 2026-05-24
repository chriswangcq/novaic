# Publish quality-gate controller code safely

## Problem

The quality-gate implementation must be committed and pushed without accidentally including unrelated dirty workspace changes. Polling must be paused first so the old API-host controller cannot process the new commit before it is upgraded.

## Success Criteria

- API-host Release Controller polling is paused before pushing the quality-gate commit.
- Local release-controller/deploy guard tests pass before commit.
- Only intended source/config/docs/test files and the active ledger are staged, with unrelated pre-existing dirty files left untouched.
- The parent commit is pushed to `origin/main` and its commit id is recorded.
- If any submodule changed intentionally, its commit/push is recorded; otherwise no submodule churn is introduced.
