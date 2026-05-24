# Package release-controller Docker image

## Problem

Create Docker image packaging for the release-controller service so it can run from an immutable image instead of source on the host.

## Success Criteria

- A release-controller Dockerfile exists in the repository.
- The image installs the `novaic-release-controller` package and runtime dependencies.
- The container starts the FastAPI app through an explicit entrypoint.
- `NOVAIC_RELEASE_CONTROLLER_CONFIG` is required at runtime.
- Local build or syntax validation proves the Dockerfile is usable.
