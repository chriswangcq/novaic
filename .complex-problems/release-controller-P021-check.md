# P021 Success Check

## Summary

P021 is successful. The API-host worktree is now a release-capable git checkout, the updated release-controller image is deployed by digest, and autonomous polling is running in dry-run mode.

## Evidence

- The API-host worktree fast-forwarded to `78411ddc0bbf`, the pushed platform source commit.
- Required Dockerfiles and image-based deploy commands exist in the worktree.
- Release-relevant submodules were initialized.
- The deployed release-controller is healthy and loopback-only.
- `/v1/status` reports autonomous polling enabled/running with no last error.
- The polling loop recorded a `poll` run for `main -> staging` at commit `78411ddc0bbf`.
- Existing prod/staging API and Factory health checks still return 200.

## Criteria Map

- API-host worktree is a git checkout: satisfied.
- Submodules needed by backend and Factory build contexts initialized: satisfied for release-relevant submodules.
- Release-controller image rebuilt, pushed, and deployed by immutable digest: satisfied.
- Deployed controller remains loopback-only and healthy: satisfied.
- Deployed controller can observe branch heads using configured repo/worktree: satisfied.
- Existing service health checks still pass: satisfied.

## Execution Map

- Bootstrapped worktree.
- Built/pushed/deployed release-controller image.
- Enabled dry-run autonomous polling.
- Published platform source to `origin/main`.
- Fast-forwarded worktree to the pushed commit.
- Verified status, paths, polling, and service health.

## Stress Test

- The first full submodule clone attempt exposed private HTTPS submodule problems; the final path uses SSH auth and initializes only release-relevant submodules.
- The controller saw many remote branches and skipped unmatched branches, preserving explicit branch-rule safety.

## Residual Risk

- Non-dry-run staging automation is intentionally not enabled; `dry_run_default=true` keeps the controller observational until that policy is flipped.

## Result IDs

- R021
