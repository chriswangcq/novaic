# Wire deployed release-controller branch polling

## Problem Definition

The deployed release-controller is safe and reachable, but branch-driven polling is not exposed by the running service. The existing `BranchPoller` needs to be wired into the HTTP control plane and verified on the API host.

## Proposed Solution

Add a `POST /v1/polls/once` endpoint that:

- builds a `GitBranchHeadProvider` from current config
- runs `BranchPoller.poll_once(dry_run=...)`
- returns changed/skipped/failed outcomes
- keeps planner safety rules as the only namespace/prod gate

For deployment verification, update API-host config to use an HTTPS git remote for branch observation if SSH credentials are not guaranteed inside the container. Keep `dry_run_default=true`.

## Acceptance Criteria

- `/v1/polls/once` exists and returns poll outcomes.
- Poll once supports `dry_run=true`.
- Poll once cannot bypass prod branch-safety checks.
- API host controller image is rebuilt/redeployed with the endpoint.
- API host `POST /v1/polls/once` returns 200.
- Docs mention branch polling verification.
- Tests/guards pass.

## Verification Plan

- Add endpoint and tests.
- Run release-controller tests and root guard.
- Rebuild/push/deploy controller image by digest.
- Update API-host config remote URL if needed.
- Verify `/v1/polls/once` on API host.

## Risks

- If the repository is private and no credential is available in the container, poll-once will fail at `git ls-remote`. Use HTTPS only if it works from API host.

## Assumptions

- Real non-dry-run branch execution still remains disabled until a managed worktree is fully prepared.
