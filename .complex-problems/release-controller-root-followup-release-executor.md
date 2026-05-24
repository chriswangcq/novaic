# Make release-controller execute real staging releases

## Problem

The deployed release-controller can poll and plan branch releases, but its container lacks a usable Docker CLI and Docker Compose plugin. Make the release-controller image capable of running its build/publish/deploy command plan, redeploy it, and prove a non-dry-run staging release path.

## Success Criteria

- Release-controller image contains working `docker` and `docker compose` commands.
- API-host controller container can access the host Docker socket.
- Updated image is built, pushed, and deployed by immutable digest.
- Non-dry-run `main -> staging` trigger can run verification/build/publish/deploy or produces a precise blocker after invoking the real command path.
- Prod remains promotion-only and cannot be branch-triggered.
- Docs mention the Docker CLI/Compose runtime dependency.
