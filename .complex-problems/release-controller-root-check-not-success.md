# Release Controller Root Not Success Check

## Summary

The release-controller work is substantially complete but not fully successful against the centered branch-driven goal. The deployed service can run manual dry-run triggers and the codebase includes a poller module, but the deployed HTTP service does not yet expose or run branch polling, and the API host worktree is not yet a managed checkout for real non-dry-run branch releases.

## Blocking Gaps

- The deployed service has no `/v1/polls/once` or background polling loop wired to `BranchPoller`.
- The API host `/opt/novaic/release-controller/worktree` is not yet a managed git checkout.
- Real non-dry-run branch releases remain disabled by `dry_run_default=true`.
- The controller is deployed and safe, but not yet actually branch-driven in production.

## Result IDs

- R017
