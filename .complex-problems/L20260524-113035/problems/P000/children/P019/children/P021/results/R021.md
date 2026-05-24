# P021 Result

## Summary

Bootstrapped the API-host managed worktree, redeployed the updated release-controller image, enabled autonomous dry-run polling, and verified the controller observed the pushed `main` commit from its own loop.

## Done

- Replaced the empty API-host worktree with a git checkout of `git@github.com:chriswangcq/novaic.git`.
- Initialized the release-relevant submodules:
  - `Entangled`
  - `novaic-agent-runtime`
  - `novaic-blob-service`
  - `novaic-business`
  - `novaic-common`
  - `novaic-cortex`
  - `novaic-device`
  - `novaic-gateway`
  - `novaic-logicalfs`
  - `novaic-sandbox-service`
  - `novaic-llm-factory`
- Built and pushed release-controller image tag `sha-802133d6a120`.
- Deployed immutable image digest `sha256:9ebe598d9dd8dca0810bc292adc825b6717a3e0041a96d60ea9e95a2e99866e1`.
- Enabled `polling_enabled=true` in API-host runtime config while keeping `dry_run_default=true`.
- Spawned and closed P023 to publish the current release platform source to `origin/main`.
- Fast-forwarded the API-host worktree to commit `78411ddc0bbf`.

## Verification

- Local checks before deployment/publish:
  - `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q` -> `35 passed`.
  - `python3 -m pytest -q scripts/ci/test_release_controller_ci.py` -> `6 passed`.
  - `python3 -m pytest -q` -> `11 passed`.
  - `bash -n deploy` -> passed.
- Release-controller deployment:
  - Container image: `127.0.0.1:5000/novaic/release-controller@sha256:9ebe598d9dd8dca0810bc292adc825b6717a3e0041a96d60ea9e95a2e99866e1`.
  - Container health: `healthy`.
  - Bind: `127.0.0.1:19880`.
  - Nginx refs to `release-controller` or `19880`: `0`.
- API-host worktree:
  - `git rev-parse --short=12 HEAD` -> `78411ddc0bbf`.
  - `git status --short --branch` -> `## main...origin/main`.
  - `docker/api-backend/Dockerfile`, `docker/llm-factory/Dockerfile`, and `docker/release-controller/Dockerfile` exist.
  - `deploy` contains `services-image`, `factory-image`, and `release-controller-image`.
- Autonomous polling:
  - `/v1/status` reports `polling.enabled=true`, `polling.running=true`, `iteration_count=6`, and `last_error=null`.
  - `branch_heads.main` is `78411ddc0bbf7097c2f89d2a4a1b6e8b017f6379`.
  - Recent run `20260524-045632-main-78411ddc0bbf` is a `poll` trigger for namespace `staging`, status `succeeded`, `dry_run=true`.
- Existing service health after redeploy:
  - `http://127.0.0.1:19999/api/health=200`
  - `http://127.0.0.1:29999/api/health=200`
  - `http://127.0.0.1:19990/health=200`
  - `http://127.0.0.1:29990/health=200`

## Known Gaps

- Autonomous polling is enabled in dry-run mode. Flipping to non-dry-run staging is now technically prepared but remains an explicit runtime policy change.

## Artifacts

- Release-controller digest: `sha256:9ebe598d9dd8dca0810bc292adc825b6717a3e0041a96d60ea9e95a2e99866e1`
- Platform source commit: `78411ddc0bbf`
- API-host worktree: `/opt/novaic/release-controller/worktree`
