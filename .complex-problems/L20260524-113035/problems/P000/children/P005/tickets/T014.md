# Deploy release-controller to API host and verify

## Problem Definition

The release-controller is implemented and packaged, but it is not yet running on the API host. It must be deployed as an internal Docker Compose control-plane service and verified without exposing public ingress.

## Proposed Solution

Bootstrap the first release-controller deployment on the API host:

- sync/build/push or otherwise make an immutable release-controller image available to the internal registry
- prepare `/opt/novaic/release-controller/config.json`
- prepare controller state/worktree directories
- deploy through `./deploy release-controller-image <immutable-image-ref>`
- verify local health and status endpoints on the API host
- confirm port binding remains loopback-only
- confirm existing prod/staging backend and factory services remain healthy

## Acceptance Criteria

- Release-controller container is running on the API host.
- `/health` returns healthy via `127.0.0.1:19880`.
- `/v1/status` returns state without errors.
- Container uses the image ref passed through deploy.
- Controller is not exposed publicly through Nginx.
- Existing prod/staging API and Factory health checks still pass.

## Verification Plan

- SSH to API host and inspect Docker availability.
- Build/push immutable controller image if needed for bootstrap.
- Write runtime config with explicit state/worktree paths.
- Run `./deploy release-controller-image <image-ref>`.
- Verify Docker Compose project/container status.
- Verify health/status endpoints.
- Verify existing service health endpoints.

## Risks

- First bootstrap may need a one-time remote build because local Docker daemon is unavailable. Record this as bootstrap-only and keep the durable deploy path image-based.
- Docker socket and worktree mounts are powerful; keep controller bound to loopback.

## Assumptions

- API host SSH access and internal Docker registry are available.
- Nginx remains host ingress and is not modified by this deployment.
