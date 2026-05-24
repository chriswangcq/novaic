# Publish persistence commit with remote polling paused

## Problem

Before the API-host controller can run the persistence change, the local source must be committed and pushed without unrelated workspace residue, and remote polling must be paused so the old controller does not auto-process the new main commit.

## Success Criteria

- API-host controller status is captured before changes, including current prod/staging pointers and polling state.
- Remote polling is disabled and verified before the new commit is pushed.
- Only intended release-controller persistence files are staged and committed locally.
- The persistence commit is pushed to `origin/main` and its hash is recorded.
- Remote controller still reports healthy status with polling disabled after the push.
