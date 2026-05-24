# Containerize and integrate release-controller deployment

## Problem

The controller must run as a Docker service on the API host and be deployable through the repository's operational tooling.

## Success Criteria

- Dockerfile and Compose package exist for release-controller.
- Runtime directories, env examples, and safe defaults are documented.
- Deploy script has release-controller install/update/status/logs commands.
- Compose rendering passes locally.
- Controller container has only the volumes needed for git working copy, release state, deploy script, Docker socket, and SSH/deploy inputs.
