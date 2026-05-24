# Migrate release-controller CI/CD docs and clean stale branches

## Problem Definition

The release-controller is now implemented and deployed, but the repository still needs operator-facing documentation for the new center-driven CI/CD path and stale local branches should be cleaned up carefully.

## Proposed Solution

Update documentation to describe:

- release-controller role and current deployed status
- self-hosted branch-driven release flow
- manual trigger, prod promotion, rollback, and dry-run behavior
- image-based deploy paths
- what still depends on existing scripts during migration

Then inspect local branches and delete stale local branches only when they are not the active branch and do not contain unmerged unique work that would be lost.

## Acceptance Criteria

- Docs describe the self-hosted release-controller path instead of treating GitHub Actions as the long-term primary path.
- Docs include current API host deployment details and health/status checks.
- Docs explain the current bootstrap limitation and next worktree requirement.
- Local stale branches are inspected before deletion.
- Current `main` branch remains active.
- No uncommitted work is reverted.

## Verification Plan

- Inspect current docs/runbooks.
- Patch release-controller architecture/runbook docs.
- Inspect local branch merge status.
- Delete only safe stale local branches.
- Run relevant tests/guards after docs and branch cleanup.

## Risks

- Branch cleanup can destroy useful local work if done blindly; inspect merge status and branch history first.
- Documentation must not overstate the controller as fully autonomous until managed worktree execution is closed.

## Assumptions

- Remote branch deletion is out of scope unless explicitly proven safe.
