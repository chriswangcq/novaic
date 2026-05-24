# Enable autonomous branch polling and managed staging release path

## Problem

The deployed release-controller can poll branch heads through `/v1/polls/once`, but the root CI/CD goal requires the controller itself to own branch-driven release orchestration. Add a service-owned polling loop that uses `poll_interval_seconds`, bootstrap and verify the API-host managed worktree, and keep prod protected from branch-triggered automation.

## Success Criteria

- Release-controller has an internal polling loop or equivalent service-owned scheduler that periodically invokes `BranchPoller`.
- The loop is explicitly configurable and test-covered.
- API-host `/opt/novaic/release-controller/worktree` is a verified git checkout with submodules ready for release commands.
- Deployed controller can observe branch heads from its own configured repo path.
- Branch-triggered automation can only target non-prod namespaces; prod remains promotion-only.
- Operational docs show how to enable, verify, pause, and inspect autonomous polling.
