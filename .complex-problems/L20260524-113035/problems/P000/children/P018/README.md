# Wire deployed release-controller branch polling

## Problem

The deployed release-controller must be able to trigger from branch heads through its own control plane, not only through manual `/v1/triggers`. Wire the existing poller into the service and prepare a managed API-host worktree so branch-driven dry-run polling is operational.

## Success Criteria

- HTTP API exposes a poll-once endpoint or a documented internal loop that invokes `BranchPoller`.
- Poll-once can run safely with `dry_run=true` and returns changed/skipped/failed outcomes.
- API host has a managed worktree path or explicit documented bootstrap command for it.
- Deployed controller can call the poll-once path successfully on the API host.
- Branch-driven polling remains non-prod only and cannot target prod.
- Docs mention how to run/verify branch polling.
