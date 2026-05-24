# Containerize and integrate release-controller deployment

## Problem Definition

The release-controller core service exists locally, but it is not yet packaged as an immutable Docker service or integrated into the API host deployment shape. It needs a Dockerfile, runtime config layout, Compose service integration, and deploy script entrypoints that can run the controller as an internal control-plane service.

## Proposed Solution

Add Docker packaging and local deployment integration for `novaic-release-controller`:

- A Dockerfile for the release-controller package.
- A runtime config template under `docker/release-controller` or equivalent.
- Compose integration that runs the service on loopback/internal port, mounts state and release directories, and does not expose it as public ingress.
- Deploy script commands for image-based release-controller deployment.
- Local validation that Docker/Compose config renders without missing required variables.

Keep the release-controller separate from runtime service discovery. It is a CI/CD control plane service, not an application dependency registry.

## Acceptance Criteria

- Release-controller has a Dockerfile that installs the package and starts the FastAPI app.
- Runtime config path is explicit through `NOVAIC_RELEASE_CONTROLLER_CONFIG`.
- Compose config includes a release-controller service with state/config/worktree mounts.
- Compose config does not expose the controller publicly through Nginx.
- Deploy script has an image-based release-controller deployment path.
- Local `docker compose config` validation passes for the release-controller deployment shape.

## Verification Plan

- Inspect existing Docker and deploy conventions before editing.
- Run syntax checks for changed shell/YAML files.
- Run `docker compose config` with sample env.
- Run release-controller tests after packaging changes.

## Risks

- Mounting the Docker socket or repo worktree is operationally sensitive; keep it explicit and internal.
- The controller must not become public ingress by accident.
- Deploy script integration must preserve existing services-image and factory-image behavior.

## Assumptions

- Remote deployment and smoke verification are handled by P005.
- CI guard wiring is handled by P004.
