# T024 Result: Release-controller execution-capable image

## Summary

Implemented the release-controller executor runtime path so the container can run real image build/push/deploy commands instead of only planning branch releases.

## Code Changes

- `docker/release-controller/Dockerfile` now installs the Docker CLI and Docker Compose plugin.
- `docker/release-controller/Dockerfile` now installs `openssh-client` and `rsync` for deploy steps that call the existing `deploy` script over SSH.
- `docker/release-controller/compose.yaml` mounts the host Docker socket and a read-only SSH directory for controller-driven deploy commands.
- `docker/release-controller/env.sample` and `deploy` include `NOVAIC_RELEASE_CONTROLLER_SSH_DIR`.
- `scripts/ci/test_release_controller_ci.py` guards the Docker CLI, Compose plugin, SSH client, rsync, Docker socket, and SSH directory mount requirements.
- `docs/architecture/release-controller.md` and `docs/runbooks/deploy.md` document the executor runtime dependency.
- `novaic-release-controller/config.sample.json` uses lightweight self-contained verify commands suitable for the controller container.

## Verification Completed

- `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q` passed: 35 tests.
- `python3 -m pytest -q scripts/ci/test_release_controller_ci.py` passed: 6 tests.
- `python3 -m pytest -q` passed: 11 tests.
- `bash -n deploy` passed.
- Built and pushed an immutable release-controller image with Docker CLI/Compose support:
  - `127.0.0.1:5000/novaic/release-controller@sha256:ccb4189018157fd48aeca1c6cf6bb455dac8f7a7dd382f9cf456469d3f5d307a`
- Deployed that digest to the API host.
- Verified inside the running controller container:
  - `docker --version` works: Docker 29.1.3.
  - `docker compose version` works: Docker Compose v2.40.3.
  - Host Docker socket access works; `docker ps` from inside the controller can see host containers.
- Exercised a real non-dry-run `main -> staging` trigger:
  - Run `20260524-051311-main-78411ddc0bbf`
  - `git-fetch` succeeded.
  - `git-checkout` succeeded.
  - `verify-1` (`bash -n deploy`) succeeded.
  - `verify-2` (`python3 -m py_compile docker/api-backend/write_env.py`) succeeded.
  - `build-api-backend` succeeded.
  - `build-llm-factory` succeeded.
  - `push-api-backend` succeeded.
  - `push-llm-factory` succeeded.
  - `deploy-api-staging` reached the real deploy command path and failed with the precise blocker: `/opt/novaic/release-controller/worktree/deploy: line 666: ssh: command not found`.

## Additional Fix Prepared

After recording the blocker, the image was further patched to include `openssh-client` and `rsync`, and the Compose package was patched to mount a read-only SSH directory. A newer image was built and pushed:

- `127.0.0.1:5000/novaic/release-controller@sha256:8bd2205a8a2b4cc21c7101f4d70ac06f410e36f5ea9837375c7ab5ff7cf7b0aa`

This newer digest still needs to be deployed and exercised with another non-dry-run staging trigger.

## Result

T024 proved that the release-controller now executes the real build/push/deploy plan through Docker and Docker Compose, and it recorded the next concrete runtime blocker after the Docker path. The follow-up is to deploy the SSH-capable digest and rerun the non-dry-run staging release to close the deploy step itself.
