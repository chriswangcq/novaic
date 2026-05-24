# Package release-controller Docker image

## Problem Definition

The release-controller package needs a Docker image so it can be deployed as an immutable control-plane service instead of running from mutable host source.

## Proposed Solution

Add `docker/release-controller/Dockerfile` that:

- uses a Python runtime base image
- installs the local `novaic-release-controller` package
- requires `NOVAIC_RELEASE_CONTROLLER_CONFIG`
- starts `release_controller.main`

Keep the Dockerfile small and compatible with building from the repository root. Add a `.dockerignore` if needed to avoid sending irrelevant local state.

## Acceptance Criteria

- Dockerfile exists under a clear release-controller Docker package.
- Dockerfile installs runtime dependencies from `novaic-release-controller/pyproject.toml`.
- Container command starts the release-controller app.
- Runtime config path remains environment-driven.
- Dockerfile validates by build or a local Dockerfile/package sanity check.

## Verification Plan

- Inspect existing Dockerfile conventions.
- Add the Dockerfile.
- Run a local Docker build if Docker is available.
- Run release-controller tests afterward.

## Risks

- Building from the wrong context could miss the package.
- Copying the whole repo into the image would make the controller image unnecessarily large and stale.

## Assumptions

- Compose and deploy wiring are handled by sibling P014 and P015.
