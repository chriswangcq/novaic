# Publish release platform source

## Problem Definition

The API-host release-controller worktree is a clean checkout of `origin/main`, but `origin/main` does not yet include the local release platform source required by the controller's command plan.

## Proposed Solution

Commit and push the platform release source needed for the controller path:

- release-controller package and tests
- Docker Compose/image packages
- image-based deploy commands
- CI guards/workflows and release docs
- active ledger evidence for this release-controller work

Avoid reverting unrelated dirty submodule work. Do not commit generated Python caches or local build artifacts.

## Acceptance Criteria

- A new commit exists on local `main`.
- The commit is pushed to `origin/main`.
- API-host worktree can fast-forward to that commit.
- API-host worktree contains current Docker/deploy release paths.
- Existing submodule dirtiness is not reset or discarded.

## Verification Plan

- Clean generated Python artifacts.
- Stage the intended platform source paths explicitly.
- Review staged names.
- Commit and push to `origin/main`.
- Fast-forward API-host worktree and check required files/commands.

## Risks

- The local worktree contains older unrelated dirty changes; staging must be explicit.

## Assumptions

- `origin/main` is the intended release-controller source branch.
