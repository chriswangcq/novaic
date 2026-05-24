# Autonomous branch polling and managed staging path

## Problem Definition

The release-controller is deployed and can run branch polling through `/v1/polls/once`, but the root CI/CD goal requires the controller itself to own the branch observation loop and the API host to have a release-ready worktree for non-dry-run staging releases.

## Proposed Solution

Split the follow-up into bounded work:

- Add a service-owned polling loop that periodically invokes `BranchPoller` using `poll_interval_seconds`.
- Make the loop explicit in config and safe by default, with tests proving startup/shutdown behavior and non-prod branch safety.
- Bootstrap and verify `/opt/novaic/release-controller/worktree` on the API host as a real git checkout with submodules.
- Redeploy the release-controller image and verify the running control plane can observe branch heads from the managed worktree.
- Update docs with enable/pause/inspect procedures for autonomous polling.

## Acceptance Criteria

- The controller can run autonomous branch polling without GitHub Actions.
- Polling behavior is configurable and observable.
- The API-host worktree is a verified checkout ready for release commands.
- Branch automation cannot target prod.
- Tests and CI guard pass.
- Deployment evidence proves the updated controller is running on the API host.

## Verification Plan

- Add focused unit tests around polling loop lifecycle and config parsing.
- Run release-controller tests, release-controller CI guard, root pytest, and `bash -n deploy`.
- Bootstrap or repair the API-host worktree.
- Build/push/deploy a new release-controller image digest.
- Verify health/status/polling evidence on `127.0.0.1:19880`.

## Risks

- A real non-dry-run staging deploy may be slow or fail if the worktree/submodules/build context are incomplete.
- The polling loop must not accidentally trigger prod; keep prod promotion separate from branch rules.

## Assumptions

- `main` remains the staging branch rule.
- `prod` remains promotion-only.
- The API host can reach `https://github.com/chriswangcq/novaic.git`.
