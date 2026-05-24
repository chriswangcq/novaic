# Release Controller Root Not Success Check 3

## Summary

The controller now owns autonomous branch polling and observes `main -> staging` without GitHub Actions, but the root CI/CD goal is not fully successful yet. A hard execution check showed the release-controller container does not currently expose a usable `docker` or `docker compose` CLI, so non-dry-run build/publish/deploy execution is not proven.

## Evidence

- R017 proves the core release-controller platform, deploy path, CI guard, deployment, docs migration, and stale branch cleanup.
- R018 proves the deployed poll-once API path.
- R023 proves autonomous dry-run polling, API-host worktree, source publish, and docs.
- API-host release-controller container check:
  - `docker exec novaic-release-controller-release_controller-1 docker --version` failed with `executable file not found in $PATH`.
  - `docker exec novaic-release-controller-release_controller-1 docker compose version` failed with `executable file not found in $PATH`.
- The host has Docker and Compose, but the controller process executes plans inside its container.

## Criteria Map

- Documented design and implementation: satisfied.
- Branch polling and deterministic branch-to-namespace mapping: satisfied.
- Verification/build/publish/deploy command support: partially satisfied; plans exist, but the runtime image lacks Docker CLI/Compose.
- Containerized and deployed on API host: satisfied.
- Staging triggered from branch change without GitHub Actions: dry-run satisfied, non-dry-run not proven.
- Prod promotion immutable refs: satisfied in planner/guards.
- GitHub Actions fallback docs: satisfied.
- Branch/deploy residue cleanup: satisfied locally.
- Runtime deployment evidence: partially satisfied; running controller is healthy, release execution runtime dependency is missing.

## Execution Map

- Reviewed R017/R018/R023.
- Performed a strict runtime execution dependency check inside the deployed controller container.
- Identified one follow-up needed to close real release execution.

## Stress Test

- Dry-run success alone would hide that non-dry-run commands cannot currently invoke Docker from the controller container.

## Residual Risk

- Until the follow-up closes, the controller is a safe autonomous dry-run orchestrator, not a fully proven non-dry-run CD executor.

## Result IDs

- R017
- R018
- R023
