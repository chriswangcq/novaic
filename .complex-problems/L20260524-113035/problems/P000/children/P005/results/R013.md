# P005 Result

## Summary

Deployed the release-controller to the API host as an internal Docker Compose control-plane service and verified health, status, image ref, loopback-only binding, and existing service health.

## Done

- Built release-controller image on API host for first bootstrap because local Docker daemon was unavailable.
- Pushed image to the API host local registry.
- Deployed through `./deploy release-controller-image` using immutable digest ref:
  - `127.0.0.1:5000/novaic/release-controller@sha256:77ec378e105166c501fe8f9f74932d7f09e622ffb2bca0d683bf854c0dcc49a0`
- Wrote runtime config at `/opt/novaic/release-controller/config.json`.
- Fixed deploy script separation between Compose package dir and runtime state dir:
  - Compose: `/opt/novaic/docker/release-controller`
  - Runtime: `/opt/novaic/release-controller`
- Started container:
  - `novaic-release-controller-release_controller-1`

## Verification

- `curl http://127.0.0.1:19880/health`
  - Returned `{"status":"healthy"}`.
- `curl http://127.0.0.1:19880/v1/status`
  - Returned 200 and state keys: `branch_heads,candidates,current_releases,previous_releases,recent_runs,state_dir`.
- Docker inspect:
  - Container image is the immutable digest ref passed to deploy.
  - Container health is `healthy`.
- Port binding:
  - `127.0.0.1:19880`.
  - `ss` shows listener on `127.0.0.1:19880`.
- Nginx:
  - `/etc/nginx` contains zero `release-controller` or `19880` refs.
- Existing internal service health:
  - `http://127.0.0.1:19999/api/health=200`
  - `http://127.0.0.1:29999/api/health=200`
  - `http://127.0.0.1:19990/health=200`
  - `http://127.0.0.1:29990/health=200`
- Controller dry-run trigger:
  - `POST /v1/triggers` for `main` returned `succeeded`, namespace `staging`, dry-run `true`, 10 command steps.

## Known Gaps

- First bootstrap image was built on the API host because the local Docker daemon was unavailable. Durable deployment path is now image-based and uses the pushed digest.
- The controller worktree directory exists but has not yet been turned into a managed git checkout for real non-dry-run branch releases.

## Artifacts

- API host container: `novaic-release-controller-release_controller-1`
- API host config: `/opt/novaic/release-controller/config.json`
- API host compose package: `/opt/novaic/docker/release-controller`
