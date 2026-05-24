# Release-controller execution-capable image

## Problem Definition

The release-controller container can plan releases but cannot execute non-dry-run plans because `docker` and `docker compose` are not available inside the container.

## Proposed Solution

- Update `docker/release-controller/Dockerfile` to install a working Docker CLI and Docker Compose plugin.
- Keep the host Docker socket mounted through the existing Compose package.
- Add a CI guard that asserts the Dockerfile includes the CLI/Compose runtime dependency.
- Rebuild, push, and deploy the updated controller image by digest.
- Verify `docker --version` and `docker compose version` inside the running container.
- Run a non-dry-run `main -> staging` trigger; if the real command path fails after Docker invocation, record the precise blocker.

## Acceptance Criteria

- `docker` works inside the release-controller container.
- `docker compose` works inside the release-controller container.
- The updated image is deployed by immutable digest.
- Non-dry-run staging release path is exercised.
- Prod remains promotion-only.

## Verification Plan

- Run release-controller tests and CI guard.
- Build/push/deploy updated image.
- Verify Docker/Compose inside the container.
- Trigger `main` with `dry_run=false` and inspect the run result.

## Risks

- Full staging release can be slow or fail in service tests/builds; failure is acceptable only if it proves the controller reached the real command path and records a precise blocker.

## Assumptions

- API host Docker socket remains mounted at `/var/run/docker.sock`.
