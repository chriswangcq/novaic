# Integrate release-controller into Compose runtime

## Problem

Add a Compose runtime shape for the release-controller that mounts explicit config/state/worktree paths and binds the control plane internally without public ingress.

## Success Criteria

- Compose config contains a `release_controller` service.
- The service uses a parameterized image ref.
- Runtime config, state directory, releases directory, repo/worktree, and Docker socket mounts are explicit.
- The controller binds to loopback or an internal-only port.
- Rendered `docker compose config` succeeds with sample environment values.
- The Compose integration does not add Nginx/public domain routing.
