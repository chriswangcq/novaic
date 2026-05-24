# Inspect and clean stale local branches

## Problem Definition

The repository has old local branches. Clean them without touching current uncommitted work or deleting unique commits blindly.

## Proposed Solution

Inspect:

- current branch
- local branch list
- branches merged into `main`
- branches not merged into `main`
- unique commit count and recent commits for each stale branch

Delete only branches that are merged into `main`. For unmerged stale branches, create archive refs before deletion only if the branch is clearly old and not the current line of work.

## Acceptance Criteria

- Current branch remains `main`.
- Branch cleanup command output is recorded.
- Merged stale branches are deleted locally.
- Unmerged branches are either preserved with reason or archived before deletion.
- Working tree changes are not reverted.

## Verification Plan

- Run branch inspection commands.
- Delete safe branches.
- Verify remaining branches and current branch.
- Run `git status --short` to confirm no worktree revert.

## Risks

- Deleting unmerged branches can lose context. Prefer preserving or archive refs when unsure.

## Assumptions

- Remote branch deletion is out of scope.
