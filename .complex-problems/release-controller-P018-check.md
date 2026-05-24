# P018 Success Check

## Summary

P018 is successful. The deployed release-controller now exposes a branch polling control-plane path, the API host can call it successfully in dry-run mode, and the worktree requirement is documented with an explicit bootstrap command.

## Evidence

- `POST /v1/polls/once` is implemented in `release_controller.service.create_app()` and invokes `BranchPoller`.
- API tests cover the poll-once route with an injected provider and verify structured outcomes.
- The API-host container is running the rebuilt digest `sha256:97cd1948122732a6aa6b973a714f33493b075d75dda8edd8fdd386078d4edeb5`.
- API-host health check returned `{"status":"healthy"}`.
- API-host poll-once call with `{"dry_run": true}` returned branch outcomes and planned `main -> staging`.
- Unmatched branches were skipped, which proves branch rules remain explicit.
- Nginx has no release-controller or `19880` public route.
- Docs now show both poll-once verification and worktree bootstrap.

## Criteria Map

- HTTP API exposes a poll-once endpoint or documented internal loop: satisfied by `POST /v1/polls/once`.
- Poll-once can run safely with `dry_run=true` and returns outcomes: satisfied by API-host dry-run output with `planned` and `skipped` statuses.
- API host has a managed worktree path or explicit documented bootstrap command: satisfied by runbook and architecture docs showing the bootstrap command for `/opt/novaic/release-controller/worktree`.
- Deployed controller can call poll-once successfully on API host: satisfied by the verified API-host `curl`.
- Branch-driven polling remains non-prod only and cannot target prod: satisfied by current branch rules where `main` maps to `staging`, `release/*` is candidate-only, and prod promotion remains a separate endpoint requiring immutable refs.
- Docs mention how to run/verify branch polling: satisfied by `docs/architecture/release-controller.md` and `docs/runbooks/deploy.md`.

## Execution Map

- Added the poll-once API route.
- Added API route test coverage.
- Redeployed the controller image to the API host.
- Verified health, loopback bind, no Nginx ingress, and branch polling dry-run.
- Updated architecture and runbook docs.

## Stress Test

- The poller saw many remote branches and skipped all unmatched branches instead of attempting accidental preview/prod releases.
- The controller remains loopback-only, so the newly exposed polling endpoint does not become a public release trigger.
- `dry_run=true` was used for the deployed branch poll, so verification exercised the release planning path without mutating staging.

## Residual Risk

- Background scheduled polling is not yet enabled; operators can use poll-once now, and a timer can be added later without changing the release model.
- Real non-dry-run branch releases remain intentionally gated behind worktree bootstrap and `dry_run_default` review.

## Result IDs

- R018
