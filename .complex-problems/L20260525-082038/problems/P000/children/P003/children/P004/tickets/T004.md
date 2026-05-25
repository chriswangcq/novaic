# Commit and push source

## Problem Definition

The fix needs to be available to Release Controller from GitHub source. Entangled is a submodule, so commit order matters.

## Proposed Solution

Commit the Entangled code/test changes first, push Entangled `main`, then stage the parent repo's updated submodule pointer and ledger artifacts, commit, and push parent `main`.

## Acceptance Criteria

- Entangled commit exists and is pushed.
- Parent commit exists and is pushed.
- Parent points to the pushed Entangled commit.
- No unrelated source changes are included.

## Verification Plan

Use `git status`, `git diff --cached`, `git log -1`, and `git submodule status` before and after commits.

## Risks

- Pushing directly to `main` assumes the current repo policy allows it.

## Assumptions

- User previously asked to work on and push `main`, and authorized autonomous execution.
