# Integrate release-controller into Compose runtime

## Problem Definition

The release-controller image needs a Compose runtime definition that can run it as an internal control-plane service with explicit mounts for config, state, release pointers, repo/worktree, and Docker socket access.

## Proposed Solution

Add `docker/release-controller/compose.yaml` and a sample environment file. The service should:

- use `NOVAIC_RELEASE_CONTROLLER_IMAGE`
- mount a namespace-independent controller config path
- mount state and release pointer directories
- mount the deploy worktree/repo path
- mount Docker socket explicitly for image build/push/deploy commands
- bind to a loopback-only host port or internal port
- avoid Nginx/public ingress changes

## Acceptance Criteria

- Compose file defines `release_controller`.
- Image, port, config path, state root, release root, worktree path, and Docker socket path are parameterized.
- Rendered `docker compose config` succeeds with sample env.
- No public Nginx route is added.
- Release-controller tests still pass.

## Verification Plan

- Inspect existing Compose conventions.
- Add Compose and sample env files.
- Run `docker compose --env-file ... config`.
- Run release-controller tests.

## Risks

- Mounting the Docker socket must be explicit and visible.
- Binding controller to public interfaces would be unsafe.

## Assumptions

- Deploy script wiring is handled by P015.
