# Managed worktree and API-host redeploy

## Problem Definition

The API-host release-controller runtime has an empty worktree directory. Release commands need a real git checkout with submodules, and the newly added polling loop needs to be deployed in a fresh image digest.

## Proposed Solution

- Replace the empty runtime worktree with a clean clone of `https://github.com/chriswangcq/novaic.git`.
- Initialize submodules so backend and Factory build contexts are available.
- Keep runtime config safe while enabling autonomous polling explicitly.
- Build a new release-controller image on the API host bootstrap path, push it to the local registry, and deploy by immutable digest.
- Verify loopback-only exposure, health, status polling fields, branch head observation, and existing service health.

## Acceptance Criteria

- `/opt/novaic/release-controller/worktree` is a git checkout and `git status --short --branch` works.
- Required submodule directories are present.
- Runtime config has `polling_enabled=true` while prod branch automation remains impossible.
- New image digest is deployed and healthy.
- `/v1/status` reports polling enabled/running with no last error after startup.
- `/v1/polls/once` still works.
- Existing prod/staging API and Factory health checks pass.

## Verification Plan

- Inspect and bootstrap the worktree on the API host.
- Run local tests before deployment.
- Build/push/deploy the updated image.
- Verify API-host release-controller health/status/polling and current service health.

## Risks

- Cloning submodules can be slow or fail if remote access changes.
- Enabling autonomous polling with `dry_run_default=true` should not mutate staging; non-dry-run enablement remains a separate runtime decision after the checkout is proven.

## Assumptions

- The API host has access to GitHub over HTTPS.
- The local Docker registry remains at `127.0.0.1:5000`.
