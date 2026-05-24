# Update release-controller CI/CD docs

## Problem

The repository needs documentation that reflects the deployed center-driven release-controller path, including current capabilities, operator commands, and remaining bootstrap limitations.

## Success Criteria

- Release-controller architecture/runbook docs mention deployed API host status.
- Docs describe branch-driven staging, manual prod promotion, rollback, dry-run behavior, and image-based deploy paths.
- Docs clarify that GitHub Actions is no longer the desired long-term primary orchestrator.
- Docs explicitly list the current managed worktree gap before real non-dry-run branch execution.
- Docs do not claim public ingress for the controller.
